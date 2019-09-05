#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# Copyright (c) 2014 Mozilla Corporation


from lib.alerttask import AlertTask
from mozdef_util.query_models import SearchQuery, TermMatch, ExistsMatch


class AlertCloudtrailExcessiveDescribe(AlertTask):
    def main(self):
        # Create a query to look back the last 20 minutes
        search_query = SearchQuery(minutes=5)

        # Add search terms to our query
        search_query.add_must([
            TermMatch('source', 'cloudtrail'),
            TermMatch('details.eventverb', 'Describe'),
            ExistsMatch('details.sourceipv4address')
        ])

        self.filtersManual(search_query)
        # We aggregate on details.sourceipv4address which is the AWS service name
        self.searchEventsAggregated('details.sourceipv4address', samplesLimit=2)
        self.walkAggregations(threshold=5)

    def onAggregation(self, aggreg):
        category = 'access'
        tags = ['cloudtrail']
        severity = 'WARNING'
        summary = "A production service is generating excessive describe calls."
        # Create the alert object based on these properties
        return self.createAlertDict(summary, category, tags, aggreg['events'], severity)
