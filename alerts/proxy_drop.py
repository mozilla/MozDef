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
from query_models import SearchQuery, TermMatch, ExistsMatch


class AlertProxyDrop(AlertTask):
    def main(self):
        search_query = SearchQuery(minutes=5)

        search_query.add_must([
            TermMatch('category', 'squid'),
            ExistsMatch('details.proxyaction'),
        ])

        self.filtersManual(search_query)

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
