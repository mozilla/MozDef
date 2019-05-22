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

        # Search aggregations on field 'details.useridentity.username', keep X samples of
        # events at most
        self.searchEventsAggregated("details.useridentity.username", samplesLimit=10)
        # alert when >= X matching events in an aggregation
        # I think it makes sense to alert every time here
        self.walkAggregations(threshold=2)

    def onEvent(self, aggreg):
        category = 'authentication'
        tags = ['cloudtrail']
        severity = 'NOTICE'

        sourceip = set()
        for event in aggreg["allevents"]:
            sourceip.add(event['_source']['details']['sourceipaddress'])

        summary = "Cloudtrail Event: Many logins by user: {0} from many IPs: {1}".format(
            aggreg["value"], ",".join(sorted(sourceip))
        )

        return self.createAlertDict(summary, category, tags, aggreg["events"], severity)
