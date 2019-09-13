#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# Copyright (c) 2014 Mozilla Corporation


from lib.alerttask import AlertTask
from mozdef_util.query_models import SearchQuery, TermMatch
import re


class AlertLdapPasswordSpray(AlertTask):
    def main(self):
        self.parse_config('ldap_password_spray.conf', ['threshold_count', 'search_depth_min'])
        search_query = SearchQuery(minutes=int(self.config.search_depth_min))
        search_query.add_must([
            TermMatch('category', 'ldap'),
            TermMatch('details.response.error', 'LDAP_INVALID_CREDENTIALS')
        ])
        self.filtersManual(search_query)
        self.searchEventsAggregated('details.client', samplesLimit=10)
        self.walkAggregations(threshold=int(self.config.threshold_count))

    def onAggregation(self, aggreg):
        category = 'ldap'
        tags = ['ldap']
        severity = 'WARNING'
        email_list = set()
        email_regex = r'.*mail=([a-zA-Z0-9._-]+@[a-zA-Z0-9._-]+\.[a-zA-Z0-9_-]+)'

        for event in aggreg['allevents']:
            for request in event['_source']['details']['requests']:
                for detail in request['details']:
                    match_object = re.match(email_regex, detail)
                    if match_object:
                        email_list.add(match_object.group(1))

        # If no emails, don't throw alert
        # if len(email_list) == 0:
        #     return None

        summary = 'LDAP Password Spray Attack in Progress from {0} targeting the following account(s): {1}'.format(
            aggreg['value'],
            ", ".join(sorted(email_list)[:10])
        )
        if len(email_list) >= 10:
            summary += '...'

        return self.createAlertDict(summary, category, tags, aggreg['events'], severity)
