#!/usr/bin/env python
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
# Copyright (c) 2014 Mozilla Corporation
#
# Contributors:
# Michal Purzynski mpurzynski@mozilla.com
#
# This code alerts on every successfully opened session for any user in the list

import datetime
from lib.alerttask import AlertTask
from query_models import SearchQuery, TermMatch, PhraseMatch, QueryStringMatch, RangeMatch


class SessionOpenedUser(AlertTask):
   
    def __init__(self):
        AlertTask.__init__(self)
        self._config = self.parse_json_alert_config('critical_users.json')

    def main(self):

        superquery = None
        run = 0

        for user in self._config['users']:
            if run == 0:
                superquery = PhraseMatch('summary', user)
            else:
                superquery |= PhraseMatch('summary', user)
            run += 1

        r1 = datetime.datetime.now().replace(hour=5, minute=50, second=00).isoformat()
        r2 = datetime.datetime.now().replace(hour=6, minute=0, second=00).isoformat()

        search_query = SearchQuery(minutes=5)

        search_query.add_must([
            TermMatch('_type', 'event'),
            TermMatch('category', 'syslog'),
            TermMatch('details.program', 'sshd'),
            QueryStringMatch('summary:"session opened"'),
        ])

        search_query.add_must_not([
            RangeMatch('utctimestamp', r1, r2)
        ])
        search_query.add_must(superquery)

        self.filtersManual(search_query)
        self.searchEventsAggregated('details.hostname', samplesLimit=10)
        self.walkAggregations(threshold=1)

    def onAggregation(self, aggreg):
        category = 'session'
        severity = 'WARNING'
        tags = ['pam', 'syslog']

        prog = ''
        for p in aggreg['events']:
            if p['_source']['details']['program'] != prog:
                prog += p['_source']['details']['program']

        summary = '{0} session opened for scanning user outside of the expected window on {1} [{2}]'.format(prog, aggreg['value'], aggreg['count'])

        return self.createAlertDict(summary, category, tags, aggreg['events'], severity)