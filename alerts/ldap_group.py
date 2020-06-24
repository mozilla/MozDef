#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# Copyright (c) 2014 Mozilla Corporation

from lib.alerttask import AlertTask
from mozdef_util.query_models import\
    PhraseMatch,\
    SearchQuery,\
    TermMatch,\
    WildcardMatch


class ldapGroupModify(AlertTask):
    def main(self):
        search_query = SearchQuery(minutes=15)

        search_query.add_must([
            TermMatch('category', 'ldapChange'),
            TermMatch('details.changetype', 'modify'),
            PhraseMatch("summary", "groups")
        ])

        # ignore test accounts and attempts to create accounts that already exist.
        search_query.add_must_not([
            WildcardMatch('details.actor', '*bind*'),
            WildcardMatch('details.changepairs', 'delete:*member*')
        ])

        self.filtersManual(search_query)
        self.searchEventsAggregated('details.email', samplesLimit=50)
        self.walkAggregations(threshold=1, config={})

    # Set alert properties
    def onAggregation(self, agg):
        email = agg['value']
        events = agg['events']

        category = 'ldap'
        tags = ['ldap']
        severity = 'INFO'

        if email is None:
            summary = 'LDAP group change detected'
        else:
            summary = 'LDAP group change initiated by {0}'.format(email)

        # Create the alert object based on these properties
        return self.createAlertDict(summary, category, tags, events, severity)
