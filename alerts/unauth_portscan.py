#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
# Copyright (c) 2017 Mozilla Corporation
#
# Contributors:
# Anthony Verez averez@mozilla.com
# Jeff Bryner jbryner@mozilla.com
# Aaron Meihm ameihm@mozilla.com
# Michal Purzynski <mpurzynski@mozilla.com>
# Alicia Smith <asmith@mozilla.com>
# Brandon Myers bmyers@mozilla.com

from lib.alerttask import AlertTask
from query_models import SearchQuery, TermMatch, ExistsMatch, PhraseMatch


class AlertUnauthPortScan(AlertTask):
    def main(self):
        self.parse_config('unauth_portscan.conf', ['url'])
        search_query = SearchQuery(minutes=30)

        search_query.add_must([
            TermMatch('_type', 'nsm'),
            TermMatch('category', 'bro'),
            TermMatch('type', 'notice'),
            ExistsMatch('details.indicators'),
            PhraseMatch('details.note', 'Scan::Port_Scan'),
        ])

        self.filtersManual(search_query)

        self.searchEventsSimple()
        self.walkEvents()

    # Set alert properties
    def onEvent(self, event):
        category = 'scan'
        severity = 'NOTICE'
        hostname = event['_source']['hostname']
        url = self.config.url

        indicators = 'unknown'
        target = 'unknown'
        x = event['_source']
        if 'details' in x:
            if 'indicators' in x['details']:
                indicators = x['details']['indicators']
            if 'destinationipaddress' in x['details']:
                target = x['details']['destinationipaddress']

        summary = '{2}: Unauthorized Port Scan Event from {0} scanning ports on host {1}'.format(indicators, target, hostname)

        # Create the alert object based on these properties
        return self.createAlertDict(summary, category, [], [event], severity, url)
