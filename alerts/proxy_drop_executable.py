#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
# Copyright (c) 2014 Mozilla Corporation


from lib.alerttask import AlertTask
from query_models import SearchQuery, TermMatch, ExistsMatch


class AlertProxyDropExecutable(AlertTask):
    def main(self):
        search_query = SearchQuery(minutes=5)

        search_query.add_must([
            TermMatch('category', 'squid'),
            TermMatch('details.proxyaction', 'TCP_DENIED/-'),
            QueryStringMatch('details.destination: /\.(exe|bin|sh|py|rb)$/')

        ])

        self.filtersManual(search_query)

       # Search aggregations on field 'hostname', keep X samples of
        # events at most
        self.searchEventsAggregated('details.sourceipaddress', samplesLimit=10)
        # alert when >= X matching events in an aggregation
        # I think it makes sense to alert every time here
        self.walkAggregations(threshold=1)

    # Set alert properties
    def onAggregation(self, aggreg):
        # aggreg['count']: number of items in the aggregation, ex: number of failed login attempts
        # aggreg['value']: value of the aggregation field, ex: toto@example.com
        # aggreg['events']: list of events in the aggregation
        category = 'squid'
        tags = ['squid', 'proxy']
        severity = 'WARNING'

        dropped_url_destinations = []

        for event in aggreg['allevents']:
            dropped_url_destinations.append(
                aggreg['allevents'][event]['_source']['details.destination'])

        summary = 'Multiple Proxy DROP events detected on {0} to the following executable file destinations: {1}'.format(
            aggreg['value'], ",".join(set(dropped_url_destinations)))

        # Create the alert object based on these properties
        return self.createAlertDict(summary, category, tags, aggreg['events'], severity)
