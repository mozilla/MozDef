#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
# Copyright (c) 2015 Mozilla Corporation
#
# Contributors:
# Aaron Meihm <ameihm@mozilla.com>
# Brandon Myers <bmyers@mozilla.com>

from lib.alerttask import AlertTask
from query_models import SearchQuery, TermMatch


class AlertGeomodel(AlertTask):
    # The minimum event severity we will create an alert for
    MINSEVERITY = 2

    def main(self):
        search_query = SearchQuery(minutes=30)

        search_query.add_must([
            TermMatch('_type', 'event'),
            TermMatch('category', 'geomodelnotice'),
        ])

        self.filtersManual(search_query)
        self.searchEventsSimple()
        self.walkEvents()

    # Set alert properties
    def onEvent(self, event):
        category = 'geomodel'
        tags = ['geomodel']
        severity = 'NOTICE'

        ev = event['_source']

        # If the event severity is below what we want, just ignore
        # the event.
        if 'details' not in ev or 'severity' not in ev['details']:
            return None
        if ev['details']['severity'] < self.MINSEVERITY:
            return None

        # By default we assign a MozDef severity of NOTICE, but up this if the
        # geomodel alert is sev 3
        if ev['details']['severity'] == 3:
            severity = 'WARNING'

        summary = ev['summary']
        alert_dict = self.createAlertDict(summary, category, tags, [event], severity)

        if 'category' in ev['details'] and ev['details']['category'].lower() == 'newcountry':
            alert_dict['details'] = {
                'locality_details': ev['details']['locality_details'],
                'category': ev['details']['category'],
                'principal': ev['details']['principal'],
                'source_ip': ev['details']['source_ipv4']
            }

        return alert_dict
