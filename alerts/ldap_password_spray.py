#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
# Copyright (c) 2014 Mozilla Corporation


from lib.alerttask import AlertTask
from mozdef_util.query_models import SearchQuery, TermMatch


class AlertLdapPasswordSpray(AlertTask):
    def main(self):
        # TODO: evaluate what the threshold should be to detect a password spray
        search_query = SearchQuery(minutes=60)

        search_query.add_must([
            TermMatch('category', 'ldap'),
            TermMatch('tags', 'ldap'),
            TermMatch('details.response.error', 'LDAP_INVALID_CREDENTIALS')
        ])

        self.filtersManual(search_query)
        self.searchEventsAggregated('details.client', samplesLimit=10)

        # TODO: evaluate what the threshold should be for this alert
        self.walkAggregations(threshold=1)

    # Set alert properties
    def onAggregation(self, aggreg):
        category = 'ldap'
        tags = ['ldap']
        severity = 'WARNING'

        user_dn_list = set()

        for event in aggreg['allevents']:
            for request in event['_source']['details']['requests']:
                user_dn_list.add(request['details'][0])

        summary = 'Possible Password Spray Attack in Progress from {0} using the following distinguished names: {1}'.format(
            aggreg['value'],
            ",".join(sorted(user_dn_list))
        )

        return self.createAlertDict(summary, category, tags, aggreg['events'], severity)
