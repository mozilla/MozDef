#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
# Copyright (c) 2014 Mozilla Corporation
#
# Contributors:
# Anthony Verez averez@mozilla.com
# Jeff Bryner jbryner@mozilla.com
# Aaron Meihm ameihm@mozilla.com
# Michal Purzynski <mpurzynski@mozilla.com>
# Alicia Smith <asmith@mozilla.com>

from lib.alerttask import AlertTask
import pyes

class AlertUnauthPortScan(AlertTask):
    def main(self):
        # look for events in last X mins
        date_timedelta = dict(minutes=30)
        # Configure filters using pyes
        must = [
            pyes.TermFilter('_type', 'bro'),
            pyes.TermFilter('category', 'bronotice'),
            pyes.TermFilter('eventsource', 'nsm'),
            pyes.ExistsFilter('details.sourceipaddress'),
            pyes.QueryFilter(pyes.MatchQuery('details.note', 'Scan::Port_Scan', 'phrase')),
        ]
        self.filtersManual(date_timedelta, must=must)
        self.searchEventsSimple()
        self.walkEvents()

    # Set alert properties
    def onEvent(self, event):
        category = 'scan'
        severity = 'NOTICE'
        hostname = event['_source']['hostname']
        url = "https://mana.mozilla.org/wiki/display/SECURITY/NSM+IR+procedures"

        sourceipaddress = 'unknown'
        target = 'unknown'
        x = event['_source']
        if 'details' in x:
            if 'sourceipaddress' in x['details']:
                sourceipaddress = x['details']['sourceipaddress']
            if 'destinationipaddress' in x['details']:
                target = x['details']['destinationipaddress']

        summary = '{2}: Unauthorized Port Scan Event from {0} scanning ports on host {1}'.format(sourceipaddress, target, hostname)

        # Create the alert object based on these properties
        return self.createAlertDict(summary, category, [], [event], severity, url)
