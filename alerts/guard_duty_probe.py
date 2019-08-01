#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# Copyright (c) 2014 Mozilla Corporation


from lib.alerttask import AlertTask
from mozdef_util.query_models import SearchQuery, TermMatch, ExistsMatch


class AlertGuardDutyProbe(AlertTask):
    def main(self):
        # Create a query to look back the last 20 minutes
        search_query = SearchQuery(minutes=20)

        # Add search terms to our query
        search_query.add_must([
            TermMatch('source', 'guardduty'),
            TermMatch('details.finding.action.actionType', 'PORT_PROBE'),
            ExistsMatch('details.sourceipaddress'),
        ])

        self.filtersManual(search_query)
        # Search aggregations on field 'sourceipaddress'
        # keep X samples of events at most
        self.searchEventsAggregated('details.sourceipaddress', samplesLimit=10)
        # alert when >= X matching events in an aggregation
        self.walkAggregations(threshold=1)

    # Set alert properties
    def onAggregation(self, aggreg):
        # aggreg['count']: number of items in the aggregation, ex: number of failed login attempts
        # aggreg['value']: value of the aggregation field, ex: toto@example.com
        # aggreg['events']: list of events in the aggregation
        category = 'bruteforce'
        tags = ['guardduty', 'bruteforce']
        severity = 'INFO'
        summary = "Guard Duty Port Probe by {}".format(aggreg['value'])

        # Create the alert object based on these properties
        return self.createAlertDict(summary, category, tags, aggreg['events'], severity)
