#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# Copyright (c) 2014 Mozilla Corporation


from lib.alerttask import AlertTask
from mozdef_util.query_models import SearchQuery, TermMatch


class AlertAuth0VerticalPasswordGuessing(AlertTask):
    def main(self):
        self.parse_config('auth0_vertical_password_guessing.conf', [
            'threshold_count',
            'search_depth_min',
            'severity',
            'user_count'])
        search_query = SearchQuery(minutes=int(self.config.search_depth_min))
        search_query.add_must_not(TermMatch('details.username', ''))
        search_query.add_must([
            TermMatch('tags', 'auth0'),
            TermMatch('details.eventname', 'Failed Login (wrong password)'),
            TermMatch('details.description', 'Wrong email or password.'),
        ])

        self.filtersManual(search_query)
        self.searchEventsAggregated('details.eventname', samplesLimit=10)
        self.walkAggregations(threshold=int(self.config.threshold_count))

    def onAggregation(self, aggreg):
        category = 'bruteforce'
        tags = ['auth0']
        severity = self.config.severity
        user_count = int(self.config.user_count)
        ip_list = set()
        user_list = set()

        for event in aggreg['allevents']:
            ip_list.add(event['_source']['details']['sourceipaddress'])
            user_list.add(event['_source']['details']['username'])

        # If it doesn't affect enough users, don't throw this alert
        if len(user_list) < user_count:
            return None

        summary = 'Auth0 Username/Password Vertical Password Guessing Attack in Progress against {0} users from {1} unique source ip(s)'.format(
            len(user_list), len(ip_list))

        return self.createAlertDict(
            summary, category, tags, aggreg['events'], severity
        )
