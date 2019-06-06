#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
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
            TermMatch('tags', 'ldap'),
            TermMatch('details.response.error', 'LDAP_INVALID_CREDENTIALS')
        ])
        self.filtersManual(search_query)
        self.searchEventsAggregated('details.client', samplesLimit=10)
        self.walkAggregations(threshold=int(self.config.threshold_count))

    # Set alert properties
    def onAggregation(self, aggreg):
        category = 'ldap'
        tags = ['ldap']
        severity = 'WARNING'

        email_list = set()

        for event in aggreg['allevents']:
            for request in event['_source']['details']['requests']:
                email = extractEmail(request['details'][0])
                if email:
                    email_list.add(extractEmail(request['details'][0]))

        # If no emails, don't throw alert
        if len(email_list) == 0:
            return None

        summary = 'Password Spray Attack in Progress from {0} targeting the following accounts: {1}'.format(
            aggreg['value'],
            ",".join(sorted(email_list))
        )

        return self.createAlertDict(summary, category, tags, aggreg['events'], severity)

    # A helper function to extract the first email in a string.
    #
    # Example:
    #
    # Input: 'dn="mail=user@example.com,o=com,dc=example"'
    # Ouput: user@example.com
    #
    def extractEmail(string):
        email_regex = r'mail=([a-zA-Z0-9._-]+@[a-zA-Z0-9._-]+\.[a-zA-Z0-9_-]+)'
        match_object = re.match(email_regex, string)

        if match_object:
            return match_object.group(1)
        else:
            return None
