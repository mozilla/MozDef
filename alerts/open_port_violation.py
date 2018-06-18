#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
# Copyright (c) 2017 Mozilla Corporation

from lib.alerttask import AlertTask
from query_models import SearchQuery, TermMatch, PhraseMatch


class AlertOpenPortViolation(AlertTask):
    def main(self):
        search_query = SearchQuery(hours=4)

        search_query.add_must([
            TermMatch('category', 'open_port_policy_violation'),
            PhraseMatch('tags', 'open_port_policy_violation')
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
        category = 'open_port_policy_violation'
        tags = ['open_port_policy_violation', 'openportpagerduty']
        severity = 'CRITICAL'

        summary = ('{0} unauthorized open port(s) on {1} ('.format(aggreg['count'], aggreg['value']))
        for event in aggreg['events'][:5]:
            summary += str(event['_source']['details']['destinationport']) + ' '
        summary += ')'

        # Create the alert object based on these properties
        return self.createAlertDict(summary, category, tags, aggreg['events'], severity)
