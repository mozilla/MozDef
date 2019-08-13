#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# Copyright (c) 2014 Mozilla Corporation
#
# This code alerts on every successfully opened session on any of the host from a given list

from lib.alerttask import AlertTask
from mozdef_util.query_models import SearchQuery, TermMatch, QueryStringMatch, PhraseMatch


class PromiscAudit(AlertTask):
    def main(self):
        search_query = SearchQuery(minutes=2)

        search_query.add_must([
            TermMatch('category', 'promiscuous'),
            PhraseMatch('summary', 'promiscuous'),
            PhraseMatch('summary', 'on')
        ])

        search_query.add_must_not([
            QueryStringMatch('details.dev: veth*'),
        ])

        self.filtersManual(search_query)
        self.searchEventsSimple()
        self.walkEvents()

    def onEvent(self, event):
        category = 'promisc'
        severity = 'WARNING'
        tags = ['promisc', 'audit']

        summary = 'Promiscuous mode enabled on {0}'.format(event['_source']['hostname'])

        return self.createAlertDict(summary, category, tags, [event], severity)
