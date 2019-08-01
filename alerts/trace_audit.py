#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# Copyright (c) 2014 Mozilla Corporation
#
# This code alerts on every successfully opened session on any of the host from a given list

from lib.alerttask import AlertTask
from mozdef_util.query_models import SearchQuery, TermMatch, PhraseMatch


class TraceAudit(AlertTask):
    def main(self):
        self.parse_config('trace_audit.conf', ['hostfilter'])
        search_query = SearchQuery(minutes=5)

        search_query.add_must([
            TermMatch('details.processname', 'strace'),
        ])

        for host in self.config.hostfilter.split():
            search_query.add_must_not(PhraseMatch('hostname', host))

        self.filtersManual(search_query)
        self.searchEventsAggregated('details.originaluser', samplesLimit=10)
        self.walkAggregations(threshold=1)

    def onAggregation(self, aggreg):
        category = 'trace'
        severity = 'WARNING'
        tags = ['audit']

        hosts = set([event['_source']['hostname'] for event in aggreg['events']])

        summary = '{0} instances of Strace or Ptrace executed by {1} on {2}'.format(
            aggreg['count'],
            aggreg['value'],
            ','.join(hosts)
        )

        return self.createAlertDict(summary, category, tags, aggreg['events'], severity)
