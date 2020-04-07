#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# Copyright (c) 2014 Mozilla Corporation


from lib.alerttask import AlertTask
from mozdef_util.query_models import SearchQuery, TermMatch


class AlertLdapBruteforceUser(AlertTask):
    def main(self):
        self.parse_config('ldap_bruteforce_user.conf', ['threshold_count', 'search_depth_min', 'host_exclusions'])
        search_query = SearchQuery(minutes=int(self.config.search_depth_min))
        search_query.add_must_not(TermMatch('details.user', ''))
        search_query.add_must([
            TermMatch('category', 'ldap'),
            TermMatch('details.response.error', 'LDAP_INVALID_CREDENTIALS'),
        ])

        for host_exclusion in self.config.host_exclusions.split(","):
            search_query.add_must_not([TermMatch("details.server", host_exclusion)])

        self.filtersManual(search_query)
        self.searchEventsAggregated('details.user', samplesLimit=10)
        self.walkAggregations(threshold=int(self.config.threshold_count))

    def onAggregation(self, aggreg):
        category = 'bruteforce'
        tags = ['ldap']
        severity = 'WARNING'
        client_list = set()

        for event in aggreg['allevents']:
            client_list.add(event['_source']['details']['client'])

        summary = 'LDAP Bruteforce Attack in Progress against user ({0}) from the following source ip(s): {1}'.format(
            aggreg['value'],
            ", ".join(sorted(client_list)[:10])
        )
        if len(client_list) >= 10:
            summary += '...'

        return self.createAlertDict(summary, category, tags, aggreg['events'], severity)
