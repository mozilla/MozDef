#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
# Copyright (c) 2014 Mozilla Corporation

from lib.alerttask import AlertTask
from query_models import SearchQuery, TermMatch
import re


class AlertHoneycomb(AlertTask):
    def main(self):
        # look for events in last 10 mins
        search_query = SearchQuery(minutes=10)

        search_query.add_must([
            TermMatch('category', 'syslog'),
            TermMatch('processname', 'Honeycomb')
        ])

        self.filtersManual(search_query)

        # Search aggregations on field 'hostname', keep X samples of
        # events at most
        self.searchEventsAggregated('hostname', samplesLimit=10)
        # alert when >= X matching events in an aggregation
        # I think it makes sense to alert every time here
        self.walkAggregations(threshold=1)

    # Set alert properties
    def onAggregation(self, aggreg):
        # aggreg['count']: number of items in the aggregation, ex: number of failed login attempts
        # aggreg['value']: value of the aggregation field, ex: toto@example.com
        # aggreg['events']: list of events in the aggregation
        category = 'honeypot'
        tags = ['honeypot', 'honeycomb']
        severity = 'WARNING'

        # This is required in order to extract and display the source IP accessing the honeypot
        pattern = '/originating_ip="(\d+\.\d+\.\d+\.\d+)"/'
        offendingIPs = []

        for event in aggreg['allevents']:
            offendingIPs.append(re.search(pattern, aggreg['allevents'][event]['_source']['summary']))

        summary = 'Honeypot activity on {0} from IP(s): {1}'.format(aggreg['value'], ",".join(set(offendingIPs)))

        # Create the alert object based on these properties
        return self.createAlertDict(summary, category, tags, aggreg['events'], severity)
