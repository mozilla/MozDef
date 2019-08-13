#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# Copyright (c) 2014 Mozilla Corporation

from lib.alerttask import AlertTask
from mozdef_util.query_models import SearchQuery, TermMatch, PhraseMatch


class AlertManyVPNDuoAuthFailures(AlertTask):
    def main(self):
        search_query = SearchQuery(minutes=2)

        search_query.add_must([
            TermMatch('category', 'event'),
            TermMatch('tags', 'duosecurity'),
            PhraseMatch('details.integration', 'global and external openvpn'),
            PhraseMatch('details.result', 'FAILURE')
        ])

        self.filtersManual(search_query)

        # Search aggregations on field 'username', keep X samples of events at most
        self.searchEventsAggregated('details.username', samplesLimit=5)
        # alert when >= X matching events in an aggregation
        self.walkAggregations(threshold=5)

    # Set alert properties
    def onAggregation(self, aggreg):
        # aggreg['count']: number of items in the aggregation, ex: number of failed login attempts
        # aggreg['value']: value of the aggregation field, ex: toto@example.com
        # aggreg['events']: list of events in the aggregation
        category = 'openvpn'
        tags = ['vpn', 'auth', 'duo']
        severity = 'NOTICE'

        summary = ('{0} openvpn authentication attempts by {1}'.format(aggreg['count'], aggreg['value']))
        sourceip = self.mostCommon(aggreg['allevents'], '_source.details.ip')
        for i in sourceip[:5]:
            summary += ' {0} ({1} hits)'.format(i[0], i[1])

        # Create the alert object based on these properties
        return self.createAlertDict(summary, category, tags, aggreg['events'], severity)
