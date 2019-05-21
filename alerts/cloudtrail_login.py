#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
# Copyright (c) 2017 Mozilla Corporation

from lib.alerttask import AlertTask
from mozdef_util.query_models import SearchQuery, TermMatch, ExistsMatch


class AlertCloudtrailLogin(AlertTask):
    def main(self):
        search_query = SearchQuery(minutes=30)

        search_query.add_must([
            TermMatch('type', 'cloudtrail'),
            TermMatch('hostname', 'signin.amazonaws.com'),
            TermMatch('category', 'AwsConsoleSignIn'),
            TermMatch('details.eventname', 'ConsoleLogin'),
            TermMatch('details.responseelements.consolelogin', 'Success'),
            ExistsMatch('details.useridentity.username')
        ])

        search_query.add_must_not(TermMatch('details.useridentity.username', 'HIDDEN_DUE_TO_SECURITY_REASONS'))

        self.filtersManual(search_query)
        self.searchEventsSimple()
        self.walkEvents()

    def onEvent(self, event):
        category = 'authentication'
        tags = ['cloudtrail']
        severity = 'NOTICE'

        # source = set()
        # for event in aggreg["allevents"]:
        #    source.add(event['_source']['details']['sourceipaddress'])

        summary = "Cloudtrail Event: Multiple successful logins"

        return self.createAlertDict(summary, category, tags, [event], severity)
