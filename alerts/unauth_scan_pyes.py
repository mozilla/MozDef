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
from query_models import SearchQuery, TermMatch, ExistsMatch, QueryFilter, MatchQuery


class AlertUnauthInternalScan(AlertTask):
    def main(self):
        search_query = SearchQuery(minutes=2)

        search_query.add_must([
            TermMatch('_type', 'bro'),
            TermMatch('category', 'bronotice'),
            TermMatch('eventsource', 'nsm'),
            TermMatch('hostname', 'nsmserver1'),
            ExistsMatch('details.sourceipaddress'),
            QueryFilter(MatchQuery('details.note', 'Scan::Address_Scan', 'phrase')),
        ])

        self.filtersManual(search_query)

        self.searchEventsSimple()
        self.walkEvents()

    # Set alert properties
    def onEvent(self, event):
        category = 'scan'
        severity = 'NOTICE'
        hostname = event['_source']['hostname']
        url = "https://mana.mozilla.org/wiki/display/SECURITY/NSM+IR+procedures"

        sourceipaddress = 'unknown'
        port = 'unknown'
        x = event['_source']
        if 'details' in x:
            if 'sourceipaddress' in x['details']:
                sourceipaddress = x['details']['sourceipaddress']
            if 'p' in x['details']:
                port = x['details']['p']

        summary = '{2}: Unauthorized Internal Scan Event from {0} scanning ports {1}'.format(sourceipaddress, port, hostname)

        # Create the alert object based on these properties
        return self.createAlertDict(summary, category, [], [event], severity, url)
