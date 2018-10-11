#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
# Copyright (c) 2014 Mozilla Corporation


from lib.alerttask import AlertTask
from query_models import QueryStringMatch, SearchQuery, TermMatch


class AlertProxyDropIP(AlertTask):
    def main(self):
        self.parse_config('proxy_drop_executable.conf', ['extensions'])

        search_query = SearchQuery(minutes=20)

        search_query.add_must([
            TermMatch('category', 'squid'),
            TermMatch('tags', 'squid'),
            TermMatch('details.proxyaction', 'TCP_DENIED/-')
        ])

        # Match on 1.1.1.1, http://1.1.1.1, or https://1.1.1.1
        ip_regex = "/^(http:\/\/|https:\/\/)?\d+\.\d+\.\d+\.\d+.*/"
        search_query.add_must([
            QueryStringMatch('details.destination: {}'.format(ip_regex))
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

        dropped_destinations = set()
        for event in aggreg['allevents']:
            dropped_destinations.add(
                event['_source']['details']['destination'])

        summary = 'Suspicious Proxy DROP event(s) detected from {0} to the following IP destination(s): {1}'.format(
            aggreg['value'],
            ",".join(sorted(dropped_urls))
        )

        # Create the alert object based on these properties
        return self.createAlertDict(summary, category, tags, aggreg['events'], severity)
