#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
# Copyright (c) 2014 Mozilla Corporation
#
# Contributors:
# Michal Purzynski mpurzynski@mozilla.com
#
# This code alerts on every successfully opened session on any of the host from a given list

from lib.alerttask import AlertTask
from query_models import SearchQuery, TermMatch, PhraseMatch
import json
import sys


class SSHFailCrit(AlertTask):
    def main(self):

        superquery = None
        with open("critical_hosts.json", "r") as fd:
            try:
                hosts_json = json.load(fd)
                run = 0
                for host in hosts_json['hosts']:
                    if run == 0:
                        superquery = PhraseMatch('details.hostname', host)
                    else:
                        superquery |= PhraseMatch('details.hostname', host)
                    run += 1
            except ValueError:
                sys.stderr.write("FAILED to open the configuration file\n")

        search_query = SearchQuery(minutes=2)

        search_query.add_must([
            TermMatch('_type', 'event'),
            TermMatch('category', 'syslog'),
            TermMatch('details.program', 'sshd'),
            PhraseMatch('summary', 'Failed'),
        ])
        search_query.add_must(superquery)

        self.filtersManual(search_query)
        self.searchEventsSimple()
        self.walkEvents()

    def onEvent(self, event):
        category = 'session'
        severity = 'CRITICAL'
        tags = ['pam', 'syslog']

        summary = 'Failed to open session on {0}'.format(event['_source']['details']['hostname'])

        return self.createAlertDict(summary, category, tags, [event], severity)

