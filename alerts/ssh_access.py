#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# Copyright (c) 2017 Mozilla Corporation

from lib.alerttask import AlertTask
from mozdef_util.query_models import SearchQuery, TermMatch, TermsMatch, PhraseMatch


class AlertSSHAccess(AlertTask):
    def main(self):
        search_query = SearchQuery(minutes=15)

        self.config = self.parse_json_alert_config('ssh_access.json')

        search_query.add_must([
            TermMatch('category', 'syslog'),
            TermMatch('details.program', 'sshd'),
            PhraseMatch('summary', 'Accepted publickey for ')
        ])

        watchedsrcips = []
        for watched in self.config['watchlist']:
            watchedsrcips.append(watched['ipaddress'])

        search_query.add_must([
            TermsMatch('details.sourceipaddress', watchedsrcips)
        ])

        self.filtersManual(search_query)
        self.searchEventsSimple()
        self.walkEvents()

    # Set alert properties
    def onEvent(self, event):
        category = 'access'
        tags = ['ssh']
        severity = 'CRITICAL'

        x = event['_source']
        if 'hostname' in x:
            hostname = x['hostname']
        if 'details' in x:
            if 'sourceipaddress' in x['details']:
                sourceipaddress = x['details']['sourceipaddress']
            if 'username' in x['details']:
                username = x['details']['username']
            else:
                username = "UNKNOWN"

        summary = 'SSH login from {0} on {1} as user {2}'.format(sourceipaddress, hostname, username)
        return self.createAlertDict(summary, category, tags, [event], severity)
