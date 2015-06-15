#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
# Copyright (c) 2014 Mozilla Corporation
#
# Contributors:
# kang@mozilla.com
#
# This script alerts when openvpn's duo security failed to contact the duo server and let the user in.
# This is a very serious warning that must be acted upon as it means MFA failed and only one factor was validated (in
# this case a VPN certificate)

from lib.alerttask import AlertTask
import pyes

class AlertDuoFailOpen(AlertTask):
    def main(self):
        # look for events in last 15 mins
        date_timedelta = dict(minutes=15)
        # Configure filters using pyes
        must = [
            pyes.QueryFilter(pyes.MatchQuery('summary','Failsafe Duo login','phrase'))
        ]
        self.filtersManual(date_timedelta, must=must)

        # Search aggregations on field 'sourceipaddress', keep X samples of events at most
        self.searchEventsAggregated('details.hostname', samplesLimit=10)
        # alert when >= X matching events in an aggregation
        # in this case, always
        self.walkAggregations(threshold=1)

    # Set alert properties
    def onAggregation(self, aggreg):
        # aggreg['count']: number of items in the aggregation, ex: number of failed login attempts
        # aggreg['value']: value of the aggregation field, ex: toto@example.com
        # aggreg['events']: list of events in the aggregation
        category = 'bypass'
        tags = ['openvpn', 'duosecurity']
        severity = 'WARNING'

        summary = 'DuoSecurity contact failed, fail open triggered on {0}'.format(aggreg['value'])

        # Create the alert object based on these properties
        return self.createAlertDict(summary, category, tags, aggreg['events'], severity)

