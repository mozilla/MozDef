#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
# Copyright (c) 2014 Mozilla Corporation
#
# Contributors:
# Jonathan Claudius jclaudius@mozilla.com
# Brandon Myers bmyers@mozilla.com
# Alicia Smith asmith@mozilla.com


from lib.alerttask import AlertTask
import pyes

class AlertProxyDrop(AlertTask):
    def main(self):
        # look for events in last X mins
        date_timedelta = dict(minutes=5)
        # Configure filters using pyes
        must = [
            pyes.TermFilter('category', 'squid'),
            pyes.ExistsFilter('details.proxyaction'),
        ]
        self.filtersManual(date_timedelta, must=must)
        self.searchEventsSimple()
        self.walkEvents()

    #Set alert properties
    def onEvent(self, event):
        category = 'squid'
        tags = ['squid']
        severity = 'WARNING'
        url = ""

        summary = event['_source']['summary']

        # Create the alert object based on these properties
        return self.createAlertDict(summary, category, tags, [event], severity, url)
