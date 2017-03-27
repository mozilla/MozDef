#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
# Copyright (c) 2014 Mozilla Corporation
#
# Contributors:
# Michal Purzynski mpurzynski@mozilla.com
#
# This code alerts on every successfully opened session on any of the host from a given list

from lib.alerttask import AlertTask
from query_models import SearchQuery, TermMatch, QueryStringMatch, PhraseMatch


class PromiscKernel(AlertTask):
    def main(self):

        search_query = SearchQuery(minutes=2)

        search_query.add_must([
            TermMatch('_type', 'event'),
            TermMatch('category', 'syslog'),
            PhraseMatch('summary', 'promiscuous'),
            PhraseMatch('summary', 'entered'),
        ])

        search_query.add_must_not([
            QueryStringMatch('summary: veth*'),
        ])

        self.filtersManual(search_query)
        self.searchEventsSimple()
        self.walkEvents()

    def onEvent(self, event):
        category = 'promisc'
        severity = 'WARNING'
        tags = ['promisc', 'kernel']

        summary = 'Promiscuous mode enabled on {0}'.format(event['_source']['hostname'])

        return self.createAlertDict(summary, category, tags, [event], severity)

