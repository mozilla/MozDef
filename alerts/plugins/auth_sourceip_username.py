# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# Copyright (c) 2017 Mozilla Corporation

import json
import os
import typing as types

from lib.config import ES
from mozdef_util.elasticsearch_client import ElasticsearchClient
from mozdef_util.query_models import SearchQuery, TermMatch, ExistsMatch
from mozdef_util.utilities.toUTC import toUTC


CONFIG_FILE = os.path.join(
    os.path.dirname(__file__),
    __file__.replace('py', 'json'),
)


# TODO: Switch to dataclass when we adopt Python 3.7+

class Config(types.NamedTuple):
    '''Expected configuration for the plugin, loaded from JSON.
    '''

    indices_to_search: types.List[str]
    search_window_hours: int
    match_tag: str

    def load(file_path: str) -> 'Config':
        '''Attempt to parse a configuration from a JSON file.
        '''

        with open(file_path) as cfg_file:
            return Config(**json.load(cfg_file))


class message(object):
    '''Alert plugin that handles any alert and attempts to enrich it with
    information about username assignments.

    This plugin will add the following fields to the alert:

    ```json
    {
        "details": {
            "usernameassignment": {
                "username": "user@mozilla.com",
                "originalip": "1.2.3.4",
            }
        }
    }
    ```
    '''

    def __init__(self):

        self.config = Config.load(CONFIG_FILE)

        self.registration = [self.config.match_tag]

        # Create a closure around an Elasticsearch client that can be invoked
        # with search terms to find events in the configured indices.
        es_client = ElasticsearchClient(ES['servers'])

        def search_fn(query):
            return query.execute(
                es_client,
                indices=self.config.indices_to_search,
            ).get('hits', [])

        self.search = search_fn

    def onMessage(self, msg):
        return enrich(
            msg,
            self.config.search_window_hours,
            self.search,
        )


def enrich(
    alert: dict,
    search_window_hours: int,
    search_fn: types.Callable[[SearchQuery], types.List[dict]],
) -> dict:
    '''Search for events that match username to
    the sourceipaddress in an alert.
    '''

    details = alert.get('details', {})

    source_ip = details.get('sourceipaddress')

    if source_ip is None:
        return alert

    search_username_assignment = SearchQuery({
        'hours': search_window_hours,
    })
    search_username_assignment.add_must([
        TermMatch('tags', 'auth0'),
        TermMatch('details.success', 'true'),
        TermMatch('details.sourceipaddress', source_ip),
        ExistsMatch('details.username'),
    ])

    assign_events = sorted(
        [hit.get('_source', {}) for hit in search_fn(search_username_assignment)],
        key=lambda evt: toUTC(evt['utctimestamp']),
        reverse=True,  # Sort into descending order from most recent to least.
    )

    if len(assign_events) == 0:
        return alert

    event = assign_events[0]

    alert['details']['username'] = event['details']['username']

    return alert
