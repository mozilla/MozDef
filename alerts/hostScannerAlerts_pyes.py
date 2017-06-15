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
import pyes

class AlertHostScannerFinding(AlertTask):
    def main(self):
        # look for events in last X mins
        date_timedelta = dict(minutes=15)
        # Configure filters using pyes
        must = [
            pyes.TermFilter('_type', 'cef'),
            pyes.ExistsFilter('details.dhost'),
            pyes.QueryFilter(pyes.MatchQuery("signatureid","sensitivefiles","phrase"))
        ]
        self.filtersManual(date_timedelta, must=must)

        # Search aggregations on field 'sourceipaddress', keep X samples of events at most
        self.searchEventsAggregated('details.dhost', samplesLimit=30)
        # alert when >= X matching events in an aggregation
        self.walkAggregations(threshold=1)

    # Set alert properties
    def onAggregation(self, aggreg):
        # aggreg['count']: number of items in the aggregation, ex: number of failed login attempts
        # aggreg['value']: value of the aggregation field, ex: toto@example.com
        # aggreg['events']: list of events in the aggregation
        category = 'hostscanner'
        tags = ['hostscanner']
        severity = 'NOTICE'

        summary = ('{0} host scanner findings on {1}'.format(aggreg['count'], aggreg['value']))
        filenames = self.mostCommon(aggreg['allevents'],'_source.details.path')
        for i in filenames[:5]:
            summary += ' {0} ({1} hits)'.format(i[0], i[1])

        # Create the alert object based on these properties
        return self.createAlertDict(summary, category, tags, aggreg['events'], severity)
