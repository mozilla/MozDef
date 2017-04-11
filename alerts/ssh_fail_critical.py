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


class SSHFailCrit(AlertTask):
    def main(self):
        hosts_json = self.parse_json_alert_config("critical_hosts.json")
        superquery = None
        for host in hosts_json['hosts']:
            if superquery is None:
                superquery = PhraseMatch('details.hostname', host)
            else:
                superquery |= PhraseMatch('details.hostname', host)

        search_query = SearchQuery(minutes=2)

        search_query.add_must([
            TermMatch('_type', 'event'),
            TermMatch('category', 'syslog'),
            TermMatch('details.program', 'sshd'),
##            ExistsMatch('details.hostname')
        ])
        search_query.add_should([
            PhraseMatch('summary', 'Failed'),
            PhraseMatch('summary', 'invalid')
        ])
        search_query.add_must(superquery)

        self.filtersManual(search_query)
        self.searchEventsAggregated('details.hostname', samplesLimit=10)
        self.walkAggregations(threshold=1)


    def onAggregation(self, aggreg):
        category = 'session'
        severity = 'WARNING'
        tags = ['pam', 'syslog']

        summary = 'Failed to open session on {1} [{0}]'.format(aggreg['count'], aggreg['value'])

        return self.createAlertDict(summary, category, tags, [event], severity)
