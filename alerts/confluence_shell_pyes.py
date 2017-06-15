#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
# Copyright (c) 2014 Mozilla Corporation
#
# Contributors:
# Jonathan Claudius jclaudius@mozilla.com

from lib.alerttask import AlertTask
import pyes

class AlertConfluenceShellUsage(AlertTask):
    def main(self):
        # look for events in last X mins
        date_timedelta = dict(minutes=5)
        # Configure filters using pyes
        must = [
            pyes.TermFilter('_type', 'auditd'),
            pyes.TermFilter('details.user', 'confluence'),
            pyes.QueryFilter(pyes.QueryStringQuery('hostname: /.*(mana|confluence).*/')),
        ]
        must_not = [
            pyes.TermFilter('details.originaluser', 'root'),
        ]
        self.filtersManual(date_timedelta, must=must, must_not=must_not)

        # Search aggregations on field 'sourceipaddress', keep X samples of events at most
        self.searchEventsAggregated('hostname', samplesLimit=10)
        # alert when >= X matching events in an aggregation
        # in this case, always
        self.walkAggregations(threshold=1)

    # Set alert properties
    def onAggregation(self, aggreg):
        # aggreg['count']: number of items in the aggregation, ex: number of failed login attempts
        # aggreg['value']: value of the aggregation field, ex: toto@example.com
        # aggreg['events']: list of events in the aggregation
        category = 'intrusion'
        tags = ['confluence', 'mana']
        severity = 'CRITICAL'

        summary = 'Confluence user is running shell commands on {0}'.format(aggreg['value'])

        # Create the alert object based on these properties
        return self.createAlertDict(summary, category, tags, aggreg['events'], severity)

