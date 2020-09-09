#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# Copyright (c) 2014 Mozilla Corporation


from lib.alerttask import AlertTask
from mozdef_util.query_models import SearchQuery, TermMatch


class AlertAuth0BruteforceUser(AlertTask):
    def main(self):
        self.parse_config('auth0_bruteforce_user.conf', ['threshold_count',
                                                         'search_depth_min',
                                                         'severity'])
        search_query = SearchQuery(minutes=int(self.config.search_depth_min))
        search_query.add_must_not(TermMatch('details.username', ''))
        search_query.add_must([
            TermMatch('tags', 'auth0'),
            TermMatch('details.eventname', 'Failed Login (wrong password)'),
        ])

        self.filtersManual(search_query)
        self.searchEventsAggregated('details.username', samplesLimit=10)
        self.walkAggregations(threshold=int(self.config.threshold_count))

    def onAggregation(self, aggreg):
        category = 'bruteforce'
        tags = ['auth0']
        severity = self.config.severity
        ip_list = set()

        for event in aggreg['allevents']:
            ip_list.add(event['_source']['details']['sourceipaddress'])

        summary = 'Auth0 Username/Password Bruteforce Attack in Progress against user ({0}) from the following source ip(s): {1}'.format(
            aggreg['value'], ", ".join(sorted(ip_list)[:10]))

        if len(ip_list) >= 10:
            summary += '...'

        return self.createAlertDict(
            summary, category, tags, aggreg['events'], severity
        )
