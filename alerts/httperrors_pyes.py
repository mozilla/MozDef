#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
# Copyright (c) 2014 Mozilla Corporation
#
# Contributors:
# Michal Purzynski michal@mozilla.com

from lib.alerttask import AlertTask
import pyes

class AlertHTTPErrors(AlertTask):
    def main(self):
        # look for events in last 15 mins
        date_timedelta = dict(minutes=15)
        # Configure filters using pyes
        must = [
            pyes.TermFilter('_type', 'bro'),
            pyes.TermFilter('eventsource', 'nsm'),
            pyes.TermFilter('category', 'bronotice'),
            pyes.ExistsFilter('details.sourceipaddress'),
            pyes.QueryFilter(pyes.MatchQuery('details.note','MozillaHTTPErrors::Excessive_HTTP_Errors_Attacker','phrase')),
        ]
        self.filtersManual(date_timedelta, must=must)

        # Search events
        self.searchEventsSimple()
        self.walkEvents()

    # Set alert properties
    def onEvent(self, event):
        category = 'httperrors'
        tags = ['http']
        severity = 'NOTICE'
        hostname = event['_source']['hostname']
        url = "https://mana.mozilla.org/wiki/display/SECURITY/NSM+IR+procedures"

        # the summary of the alert is the same as the event
        summary = '{0} {1}'.format(hostname, event['_source']['summary'])

        # Create the alert object based on these properties
        return self.createAlertDict(summary, category, tags, [event], severity=severity, url=url)

