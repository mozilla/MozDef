# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# Copyright (c) 2014 Mozilla Corporation

import json
import os
import typing as types

from lib.config import ES
from mozdef_util.query_models import PhraseMatch, SearchQuery, TermMatch
from mozdef_util.elasticsearch_client import ElasticsearchClient


CONFIG_FILE = os.path.join(
    os.path.dirname(__file__),
    'possible_usernames.json')


# TODO: Switch to dataclasses when we move to Python 3.7+


class Config(types.NamedTuple):
    '''Container for the configuration required by the plugin.
    '''

    search_window_hours: int
    indices_to_search: types.List[str]

    def load(path: str) -> 'Config':
        '''Attempt to load a `Config` from a JSON file.
        '''

        with open(path) as cfg_file:
            return Config(**json.load(cfg_file))


class message:
    '''Alert plugin that attempts to enrich any alert with a new
    `details.possible_usernames` field containing a list of names of users who
    have connected to the host described in the alert within some window of
    time.
    '''

    def __init__(self):
        self.registration = ['promisckernel']

        self._config = Config.load(CONFIG_FILE)

        self._es_client = ElasticsearchClient(ES['servers'])

    def onMessage(self, message):
        hostname = _most_common_hostname(message.get('events', []))

        query = SearchQuery(hours=self._config.search_window_hours)

        query.add_must([
            TermMatch('category', 'syslog'),
            TermMatch('hostname', hostname),
            TermMatch('details.program', 'sshd'),
            PhraseMatch('summary', 'Accepted publickey for '),
        ])

        results = query.execute(
            self._es_client, indices=self._config.indices_to_search)

        events = [
            hit.get('_source', {})
            for hit in results.get('hits', [])
        ]

        return enrich(message, events)


def enrich(alert: dict, syslog_evts: types.List[dict]) -> dict:
    '''Scan syslog events looking for usernames and append them to an alert's
    new `details.possible_usernames` field.
    '''

    summary = alert.get('summary', '')

    details = alert.get('details', {})

    scan_results = [
        evt.get('details', {}).get('username')
        for evt in syslog_evts
    ]

    possible_usernames = list(set([
        username
        for username in scan_results
        if username is not None
    ]))

    details['possible_usernames'] = possible_usernames

    alert['details'] = details

    if len(possible_usernames) > 0:
        alert['summary'] = '{}; Possible users: {}'.format(
            summary,
            ', '.join(possible_usernames),
        )

    return alert


def _most_common_hostname(events: types.List[dict]) -> types.Optional[str]:
    findings = {}

    for event in events:
        host = event.get('documentsource', {}).get('hostname')

        if host is None:
            continue

        findings[host] = (findings[host] + 1) if host in findings else 1

    # Sorting a list of (int, str) pairs results in a sort on the int.
    sorted_findings = sorted(
        [(count, hostname) for hostname, count in findings.items()],
        reverse=True)

    if len(sorted_findings) == 0:
        return None

    return sorted_findings[0][1]
