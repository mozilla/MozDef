#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
# Copyright (c) 2014 Mozilla Corporation


from lib.alerttask import AlertTask
from query_models import QueryStringMatch, SearchQuery, TermMatch
import re


class AlertProxyDropIP(AlertTask):
    def main(self):
        search_query = SearchQuery(minutes=20)

        search_query.add_must([
            TermMatch('category', 'squid'),
            TermMatch('tags', 'squid'),
            TermMatch('details.proxyaction', 'TCP_DENIED/-')
        ])

        # Match on 1.1.1.1, http://1.1.1.1, or https://1.1.1.1
        # This will over-match on short 3-char domains like foo.bar.baz.com, but will get weeded out below
        ip_regex = '/.*\..{1,3}\..{1,3}\..{1,3}(:.*|\/.*)/'
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

        # Lucene search has a slight potential for overmatches, so we'd double-check
        # with this pattern to ensure it's truely an IP before we add dest to our dropped list
        pattern = r'(http:\/\/|https:\/\/|)\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}'

        dropped_destinations = set()

        for event in aggreg['allevents']:
            if re.search(pattern, event['_source']['details']['destination']):
                dropped_destinations.add(
                    event['_source']['details']['destination'])

        # If it's all over-matches, don't throw the alert
        if len(dropped_destinations) == 0:
            return None

        summary = 'Suspicious Proxy DROP event(s) detected from {0} to the following IP-based destination(s): {1}'.format(
            aggreg['value'],
            ",".join(sorted(dropped_destinations))
        )

        # Create the alert object based on these properties
        return self.createAlertDict(summary, category, tags, aggreg['events'], severity)
