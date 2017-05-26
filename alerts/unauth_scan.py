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


class AlertUnauthInternalScan(AlertTask):
    def main(self):
        self.parse_config('unauth_scan.conf', ['nsm_host', 'url'])

        search_query = SearchQuery(minutes=2)

        search_query.add_must([
            TermMatch('_type', 'bro'),
            TermMatch('category', 'bronotice'),
            TermMatch('eventsource', 'nsm'),
            TermMatch('hostname', self.config.nsm_host),
            ExistsMatch('details.indicators'),
            PhraseMatch('details.note', 'Scan::Address_Scan'),
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
        port = 'unknown'
        x = event['_source']
        if 'details' in x:
            if 'indicators' in x['details']:
                indicators = x['details']['indicators']
            if 'p' in x['details']:
                port = x['details']['p']

        summary = '{2}: Unauthorized Internal Scan Event from {0} scanning ports {1}'.format(indicators, port, hostname)

        # Create the alert object based on these properties
        return self.createAlertDict(summary, category, [], [event], severity, url)
