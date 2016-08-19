#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
# Copyright (c) 2014 Mozilla Corporation
#
# Contributors:
# Anthony Verez averez@mozilla.com

from lib.alerttask import AlertTask
from query_models import SearchQuery


class AlertBroNotice(AlertTask):
    def main(self):
        search_query = SearchQuery(minutes=30)

        self.filtersFromKibanaDash(search_query, 'bro_notice_dashboard.json')

        # Search events
        self.searchEventsSimple()
        self.walkEvents()

    # Set alert properties
    def onEvent(self, event):
        category = 'bro'
        tags = ['bro']
        severity = 'NOTICE'

        # the summary of the alert is the one of the event
        summary = event['_source']['summary']

        # Create the alert object based on these properties
        return self.createAlertDict(summary, category, tags, [event], severity)
