#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# Copyright (c) 2017 Mozilla Corporation

from lib.alerttask import AlertTask
from mozdef_util.query_models import SearchQuery, TermMatch, PhraseMatch, QueryStringMatch
import re


class AlertAuthSignRelengSSH(AlertTask):
    def main(self):
        search_query = SearchQuery(minutes=15)

        self.config = self.parse_json_alert_config('ssh_access_signreleng.json')

        if self.config['channel'] == '':
            self.config['channel'] = None

        search_query.add_must([
            TermMatch('tags', 'releng'),
            TermMatch('details.program', 'sshd'),
            QueryStringMatch('hostname: /{}/'.format(self.config['hostfilter'])),
            PhraseMatch('summary', 'Accepted publickey for ')
        ])

        for exclusion in self.config['exclusions']:
            exclusion_query = None
            for key, value in exclusion.items():
                phrase_exclusion = PhraseMatch(key, value)
                if exclusion_query is None:
                    exclusion_query = phrase_exclusion
                else:
                    exclusion_query = exclusion_query + phrase_exclusion

            search_query.add_must_not(exclusion_query)

        self.filtersManual(search_query)
        self.searchEventsSimple()
        self.walkEvents()

    # Set alert properties
    def onEvent(self, event):
        category = 'access'
        tags = ['ssh']
        severity = 'NOTICE'

        targethost = 'unknown'
        sourceipaddress = 'unknown'
        x = event['_source']
        if 'hostname' in x:
            targethost = x['hostname']
        if 'details' in x:
            if 'sourceipaddress' in x['details']:
                sourceipaddress = x['details']['sourceipaddress']

        targetuser = 'unknown'
        found_usernames = re.findall(r'Accepted publickey for ([A-Za-z0-9]+) from', event['_source']['summary'])
        if len(found_usernames) > 0:
            targetuser = found_usernames[0]

        summary = 'SSH login from {0} on {1} as user {2}'.format(sourceipaddress, targethost, targetuser)
        return self.createAlertDict(summary, category, tags, [event], severity, channel=self.config['channel'])
