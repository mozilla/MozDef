# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# Copyright (c) 2017 Mozilla Corporation


import json
import os

from lib.config import ES
from mozdef_util.query_models import SearchQuery, TermMatch
from mozdef_util.elasticsearch_client import ElasticsearchClient


CONFIG_FILE = os.path.join(
    os.path.dirname(__file__),
    'port_scan_enrichment.json')


class message(object):
    '''Alert plugin that handles messages (alerts) tagged as containing
    information about a port scan having been detected.  This plugin
    will add information to such alerts describing any connections
    successfully established by the IP address from which the port
    scan originates.

    The expected format of the configuration file,
    `port_scan_enrichment.json`, is as such:

    ```json
    {
      "indicesToSearch": [
        "events-weekly"
      ],
      "maxConnections": 32,
      "matchTags": [
        "portscan"
      ],
      "searchWindow": {
        "hours": 12,
        "minutes": 30,
        "seconds": 59
      }
    }
    ```

    `indicesToSearch` is an array of names of indices to search in ES.
    If not provided or else an empty array, it defaults to `["events-weekly"]`.
    `maxConnections` is the maximum number of successful
    connections to list.  If set to 0, all will be listed.
    `matchTags` is a list of tags to match against.  This plugin will
    run against any alert containing any of the specified tags.  If
    `matchTags` is not provided or is an empty array, it will default
    to `["portscan"]`
    The `searchWindow` option is an object containing keyword
    arguments to be passed to Python's `datetime.timedelta` function
    and can thus contain any keys corresponding to the keyword
    arguments that would be passed to the `datetime.datetime` function.
    If `searchWindow` is not present or is an empty object, the
    default search window is 24 hours.

    The modified alert will have a `details.recentconnections` field
    appended to it, formatted like so:

    ```json
    {
      "details": {
        "recentconnections": [
          {
            "destinationipaddress": "1.2.3.4",
            "destinationport": 80,
            "timestamp": "2016-07-13 22:33:31.625443+00:00"
          }
        ]
      }
    }
    ```

    That is, each connection will be described in an array and be an
    object containing the IP address and port over which the connection
    was established and the time the connection was made.
    '''

    def __init__(self):
        # Run plugin on portscan alerts
        self.registration = ['portscan']

        config = _load_config(CONFIG_FILE)

        es_client = ElasticsearchClient(ES['servers'])

        search_indices = config.get('searchIndices', [])

        self.max_connections = config.get('maxConnections', 0)
        self.match_tags = config.get('matchTags', [])
        self.search_window = config.get('searchWindow', {})

        if len(search_indices) == 0:
            search_indices = ['alerts']

        if self.max_connections == 0:
            self.max_connections = None

        if len(self.match_tags) == 0:
            self.match_tags = ['portscan']

        if len(self.search_window) == 0:
            self.search_window = {'hours': 24}

        # Store our ES client in a closure bound to the plugin object.
        # The intent behind this approach is to make the interface to
        # the `enrich` function require dependency injection for testing.
        def search_fn(query):
            return query.execute(es_client, indices=search_indices)

        self.search = search_fn

    def onMessage(self, message):
        alert_tags = message.get('tags', [])

        should_enrich = any([
            tag in alert_tags
            for tag in self.match_tags
        ])

        if should_enrich:
            return enrich(
                message,
                self.search,
                self.search_window,
                self.max_connections)

        return message


def _load_config(file_path):
    '''Private

    Load the alert plugin configuration from a file.
    '''

    with open(file_path) as config_file:
        return json.load(config_file)


def take(ls, n_items=None):
    '''Take only N items from a list.'''

    if n_items is None:
        return ls

    return ls[:n_items]


def enrich(alert, search_fn, search_window, max_connections):
    '''Enrich an alert with information about recent connections made by
    the 'details.sourceipaddress'.

    `search_fn` is expected to be a function that accepts a single argument,
    a `SearchQuery` object, and returns a list of results from Elastic Search.

    `search_window` is expected to be a dictionary specifying the amount of
    time into the past to query for events.

    `max_connections` is expected to be the maximum number of connections to
    list in the modified alert or else `None` if no limit should be applied.

    Returns a modified alert based on a copy of the original.
    '''

    search_query = SearchQuery(**search_window)

    search_query.add_must([
        TermMatch('category', 'bro'),
        TermMatch('source', 'conn'),
        TermMatch(
            'details.sourceipaddress',
            alert['events'][0]['documentsource']['details']['sourceipaddress'])
    ])

    results = search_fn(search_query)

    events = [
        hit.get('_source', {})
        for hit in results.get('hits', [])
    ]

    details = alert.get('details', {})

    details['recentconnections'] = [
        {
            'destinationipaddress': event['details']['destinationipaddress'],
            'destinationport': event['details']['destinationport'],
            'timestamp': event['timestamp']
        }
        for event in take(events, max_connections)
    ]

    alert['details'] = details

    return alert
