#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
# Copyright (c) 2014 Mozilla Corporation
#
# Contributors:
# Anthony Verez averez@mozilla.com

from lib.alerttask import AlertTask
import pyes

class AlertFail2ban(AlertTask):
    def main(self):
        # look for events in last 10 mins
        date_timedelta = dict(minutes=10)
        # Configure filters using pyes
        must = [
            pyes.TermFilter('_type', 'event'),
            pyes.TermFilter('program', 'fail2ban'),
            pyes.QueryFilter(pyes.MatchQuery("summary","banned for","phrase"))
        ]
        self.filtersManual(date_timedelta, must=must)

        # Search events
        self.searchEventsSimple()
        self.walkEvents()

    # Set alert properties
    def onEvent(self, event):
        category = 'fail2ban'
        tags = ['fail2ban']
        severity = 'NOTICE'

        summary='{0}: {1}'.format(event['_source']['details']['hostname'], event['_source']['summary'].strip())

        # Create the alert object based on these properties
        return self.createAlertDict(summary, category, tags, [event], severity)
