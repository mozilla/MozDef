# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# Copyright (c) 2017 Mozilla Corporation


import json
import os
import typing

from lib.config import ES
from mozdef_util.elasticsearch_client import ElasticsearchClient
from mozdef_util.query_models import QueryStringMatch, SearchQuery, TermMatch
from mozdef_util.utilities.toUTC import toUTC


CONFIG_FILE = os.path.join(
    os.path.dirname(__file__), __file__.replace('py', 'json'))


# TODO: Switch to a dataclass when we adopt Python 3.7+

class Config(typing.NamedTuple):
    '''Expected configuration for the plugin, loaded from JSON.
    '''

    indices_to_search: typing.List[str]
    search_window_hours: int

    def load(file_path: str) -> 'Config':
        '''Attempt to open a JSON file and load its contents into a Config.
        '''

        with open(file_path) as cfg_file:
            return Config(**json.load(cfg_file))


class message(object):
    '''Alert plugin that handles messages (alerts) that we want to enrich with
    information about DHCP IP loans.  Where possible, adding information about
    the MAC address and the user to whom an IP was assigned can make triaging,
    for example port scan alerts, substantially easier.

    This plugin will add the following fields to the alert:

    ```json
    {
        "details": {
            "ipassignment": {
                "mac": "ab12ce34de56f",
                "user": "user@mozilla.com"
            }
        }
    }
    ```

    The plugin will also append the above information to the summary like so:

    ```
    <original summary>; IP assigned to <user> (<mac>)
    ```

    so that, for example,

    > "Port scan from 1.2.3.4"

    becomes

    > "Port scan from 1.2.3.4; IP assigned to user@mozilla.com (ab12ce34de56f)

    Finally, the plugin also sets `details.username` to the user found.
    '''

    def __init__(self):
        self.registration = ['portscan']

        self.config = Config.load(CONFIG_FILE)

        # Create a closure around an Elasticsearch client that can be invoked
        # with search terms to find events in the configured indices.
        es_client = ElasticsearchClient(ES['servers'])

        def search_fn(query):
            return query.execute(
                es_client, indices=self.config.indices_to_search)

        self.search = search_fn

    def onMessage(self, msg):
        return enrich(msg, self.config.search_window_hours, self.search)


def enrich(alert, search_window_hours, search_fn):
    '''Search for events describing the DHCP assignment for an IP in an alert
    and add information to the alert's details and summary.
    '''

    # First, we must find the MAC address that requested the offending IP
    # address listed in the alert.

    ip = alert['events'][0]['documentsource']['details']['sourceipaddress']
    search_mac_assignment = SearchQuery({'hours': search_window_hours})
    search_mac_assignment.add_must([
        TermMatch('source', 'dhcp'),
        TermMatch('details.assigned_addr', ip)
    ])

    assign_events = sorted(
        [
            hit.get('_source', {})
            for hit in search_fn(search_mac_assignment).get('hits', [])
        ],
        key=lambda evt: evt['details']['ts'],
        reverse=True)  # Sort into descending order from most recent to least.

    if len(assign_events) > 0:
        mac = assign_events[0]['details']['mac']
    else:
        return alert

    # Next, we attempt to look up the name of the user who owns the MAC address
    # in question.  When we cannot find a user, we substitute the string
    # "(no user found)"

    no_user_found = '(no user found)'

    search_mac_owner = SearchQuery({'hours': search_window_hours})
    query = 'source:local1 AND "{}"'.format(mac)
    search_mac_owner.add_must(QueryStringMatch(query))

    user_events = sorted(
        [
            hit.get('_source', {})
            for hit in search_fn(search_mac_owner).get('hits', [])
        ],
        key=lambda evt: toUTC(evt['receivedtimestamp']),
        reverse=True)  # Sort into descending order from most recent to least.

    if len(user_events) > 0:
        summary_dict = _comma_eq_dict(user_events[0]['summary'])
        user = summary_dict.get('user_name', no_user_found)
    else:
        return alert

    # Finally, add the details.ipassignment fields and append to the summary.

    if 'details' not in alert:
        alert['details'] = {}

    alert['details']['ipassignment'] = {
        'mac': mac,
        'user': user
    }

    if user != no_user_found:
        alert['details']['username'] = user

    alert['summary'] += '; IP assigned to {} ({})'.format(user, mac)

    return alert


def _comma_eq_dict(s: str) -> typing.Dict[str, str]:
    '''Parse a string formatted like `a=b,x=y z` into a dictionary such as
    `{'a': 'b', 'x': 'y z'}`.  Note that all values are treated as strings.
    '''

    return dict([
        pair.split('=')
        for pair in s.split(',')
        if '=' in pair
    ])
