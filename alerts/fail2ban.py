#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
# Copyright (c) 2014 Mozilla Corporation
#
# Contributors:
# Anthony Verez averez@mozilla.com

from lib.alerttask import AlertTask

class AlertFail2ban(AlertTask):
    def main(self):
        # look for events in last 10 mins
        date_timedelta = dict(minutes=10)
        # Configure filters by importing a kibana dashboard
        self.filtersFromKibanaDash('fail2ban_dashboard.json', date_timedelta)

        # Search events
        self.searchEventsSimple()
        self.walkEvents()

    # Set alert properties
    def onEvent(self, event):
        category = 'fail2ban'
        tags = ['fail2ban']
        severity = 'NOTICE'

        # the summary of the alert is the same as the event
        summary = event['_source']['summary']

        # Create the alert object based on these properties
        return self.createAlertDict(summary, category, tags, [event], severity)