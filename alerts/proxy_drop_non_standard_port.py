#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
# Copyright (c) 2014 Mozilla Corporation


from lib.alerttask import AlertTask
from query_models import SearchQuery, TermMatch, ExistsMatch


class AlertProxyDropNonStandardPort(AlertTask):
    def main(self):
        search_query = SearchQuery(minutes=5)

        search_query.add_must([
            TermMatch('category', 'squid'),
            TermMatch('details.proxyaction', 'TCP_DENIED/-'),
            TermMatch('details.tcpaction', 'CONNECT'),
        ])

        search_query.add_must_not([
            PhraseMatch('details.destination', ':443')
        ])

        self.filtersManual(search_query)

        # Search aggregations on field 'ip', keep X samples of events at most
        self.searchEventsAggregated('details.sourceipaddress', samplesLimit=10)
        # alert when >= X matching events in an aggregation
        self.walkAggregations(threshold=1)

    # Set alert properties
    def onAggregation(self, aggreg):
        # aggreg['count']: number of items in the aggregation, ex: number of failed login attempts
        # aggreg['value']: value of the aggregation field, ex: toto@example.com
        # aggreg['events']: list of events in the aggregation
        category = 'squid'
        tags = ['squid', 'proxy']
        severity = 'WARNING'

        destinations = []

        for event in aggreg['allevents']:
           destinations.append(event['_source']['details.destination'])

        summary = ('Suspicious proxy activity from {0} attempting to reach non-std services: {1}'.format(aggreg['value'], join(", ", destinations))

        return self.createAlertDict(summary, category, tags, aggreg['events'], severity)
