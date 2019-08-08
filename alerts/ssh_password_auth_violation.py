#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# Copyright (c) 2017 Mozilla Corporation

from lib.alerttask import AlertTask
from mozdef_util.query_models import SearchQuery, TermMatch, PhraseMatch


class AlertSSHPasswordAuthViolation(AlertTask):
    def main(self):
        search_query = SearchQuery(hours=4)

        search_query.add_must([
            TermMatch('category', 'ssh_password_auth_policy_violation'),
            PhraseMatch('tags', 'ssh_password_auth_policy_violation')
        ])

        self.filtersManual(search_query)

        # Search aggregations on field 'sourceipaddress', keep X samples of
        # events at most
        self.searchEventsAggregated('details.destinationipaddress', samplesLimit=100)
        # alert when >= X matching events in an aggregation
        self.walkAggregations(threshold=1)

    # Set alert properties
    def onAggregation(self, aggreg):
        # aggreg['count']: number of items in the aggregation, ex: number of failed login attempts
        # aggreg['value']: value of the aggregation field, ex: toto@example.com
        # aggreg['events']: list of events in the aggregation
        category = 'ssh_password_auth_policy_violation'
        tags = ['ssh_password_auth_policy_violation']
        severity = 'WARNING'
        summary = 'SSH password authentication allowed on {0}'.format(aggreg['value'])

        # Create the alert object based on these properties
        return self.createAlertDict(summary, category, tags, aggreg['events'], severity)
