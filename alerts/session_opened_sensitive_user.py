#!/usr/bin/env python
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# Copyright (c) 2014 Mozilla Corporation
#
# This code alerts on every successfully opened session for any user in the list

import datetime
from lib.alerttask import AlertTask
from mozdef_util.query_models import SearchQuery, TermMatch, PhraseMatch, QueryStringMatch, RangeMatch


class SessionOpenedUser(AlertTask):

    def __init__(self):
        AlertTask.__init__(self)
        self._config = self.parse_json_alert_config('critical_users.json')

    def main(self):

        superquery = None
        run = 0

        for user in self._config['users'].values():
            if run == 0:
                superquery = PhraseMatch('summary', user)
            else:
                superquery |= PhraseMatch('summary', user)
            run += 1

        search_query = SearchQuery(minutes=10)

        search_query.add_must([
            TermMatch('category', 'syslog'),
            TermMatch('details.program', 'sshd'),
            QueryStringMatch('summary:"session opened"')
        ])

        for expectedtime in self._config['scan_expected'].values():
            r1 = datetime.datetime.now().replace(hour=int(expectedtime['start_hour']), minute=int(expectedtime['start_minute']), second=int(expectedtime['start_second'])).isoformat()
            r2 = datetime.datetime.now().replace(hour=int(expectedtime['end_hour']), minute=int(expectedtime['end_minute']), second=int(expectedtime['end_second'])).isoformat()
            search_query.add_must_not([
                RangeMatch('utctimestamp', r1, r2)
            ])

        search_query.add_must(superquery)

        self.filtersManual(search_query)
        self.searchEventsAggregated('details.program', samplesLimit=10)
        self.walkAggregations(threshold=1)

    def onAggregation(self, aggreg):
        category = 'session'
        severity = 'WARNING'
        tags = ['pam', 'syslog']

        uniquehosts = []
        sorted_events = sorted(aggreg['events'], key=lambda x: x['_source']['hostname'])
        for e in sorted_events:
            if e['_source']['hostname'] not in uniquehosts:
                uniquehosts.append(e['_source']['hostname'])

        summary = 'Session opened by a sensitive user outside of the expected window - sample hosts: {0} [total {1} hosts]'.format(' '.join(uniquehosts), aggreg['count'])

        return self.createAlertDict(summary, category, tags, aggreg['events'], severity)
