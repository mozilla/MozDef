#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
# Copyright (c) 2014 Mozilla Corporation
#
# Contributors:
# Anthony Verez averez@mozilla.com

from lib.alerttask import AlertTask
from lib.query_classes import SearchQuery


class AlertBruteforceSsh(AlertTask):
    def main(self):
        search_query = SearchQuery(minutes=15)

        self.filtersFromKibanaDash(search_query, 'bruteforce_ssh_dashboard.json')

        # Search aggregations on field 'sourceipaddress', keep 50 samples of events at most
        self.searchEventsAggregated('sourceipaddress', samplesLimit=50)
        # alert when >= 5 matching events in an aggregation
        self.walkAggregations(threshold=2)

    # Set alert properties
    def onAggregation(self, aggreg):
        # aggreg['count']: number of items in the aggregation, ex: number of failed login attempts
        # aggreg['value']: value of the aggregation field, ex: toto@example.com
        # aggreg['events']: list of events in the aggregation
        category = 'bruteforce'
        tags = ['ssh']
        severity = 'NOTICE'

        summary = ('{0} ssh bruteforce attempts by {1}'.format(aggreg['count'], aggreg['value']))
        # append first 3 hostnames
        for e in aggreg['events'][:3]:
            if 'details' in e.keys() and 'hostname' in e['details']:
                summary += ' on {0}'.format(e['_source']['details']['hostname'])

        # Create the alert object based on these properties
        return self.createAlertDict(summary, category, tags, aggreg['events'], severity)