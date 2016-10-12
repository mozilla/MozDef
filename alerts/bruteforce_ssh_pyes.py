#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
# Copyright (c) 2014 Mozilla Corporation
#
# Contributors:
# Anthony Verez averez@mozilla.com
# Jeff Bryner jbryner@mozilla.com

from lib.alerttask import AlertTask
from query_models import SearchQuery, TermMatch, PhraseMatch


class AlertBruteforceSshES(AlertTask):
    def main(self):
        search_query = SearchQuery(minutes=2)

        search_query.add_must([
            TermMatch('_type', 'event'),
            PhraseMatch('summary', 'login invalid ldap_count_entries'),
            TermMatch('program', 'sshd'),
        ])

        search_query.add_must_not([
            PhraseMatch('summary', '10.22.75.203'),
            PhraseMatch('summary', '10.8.75.144'),
        ])

        self.filtersManual(search_query)

        # Search aggregations on field 'sourceipaddress', keep X samples of
        # events at most
        self.searchEventsAggregated('details.sourceipaddress', samplesLimit=10)
        # alert when >= X matching events in an aggregation
        self.walkAggregations(threshold=10)

    # Set alert properties
    def onAggregation(self, aggreg):
        # aggreg['count']: number of items in the aggregation, ex: number of failed login attempts
        # aggreg['value']: value of the aggregation field, ex: toto@example.com
        # aggreg['events']: list of events in the aggregation
        category = 'bruteforce'
        tags = ['ssh']
        severity = 'NOTICE'

        summary = ('{0} ssh bruteforce attempts by {1}'.format(
            aggreg['count'], aggreg['value']))
        hosts = self.mostCommon(
            aggreg['allevents'], '_source.details.hostname')
        for i in hosts[:5]:
            summary += ' {0} ({1} hits)'.format(i[0], i[1])

        # Create the alert object based on these properties
        return self.createAlertDict(summary, category, tags, aggreg['events'], severity)
