#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
# Copyright (c) 2017 Mozilla Corporation

from lib.alerttask import AlertTask
from query_models import SearchQuery, TermMatch


class AlertCloudtrailLoggingDisabled(AlertTask):
    def main(self):
        search_query = SearchQuery(minutes=30)

        search_query.add_must([
            TermMatch('_type', 'cloudtrail'),
            TermMatch('eventName', 'StopLogging'),
        ])

        search_query.add_must_not(TermMatch('errorCode', 'AccessDenied'))

        self.filtersManual(search_query)
        self.searchEventsSimple()
        self.walkEvents()

    def onEvent(self, event):
        category = 'AWSCloudtrail'
        tags = ['cloudtrail', 'aws', 'cloudtrailpagerduty']
        severity = 'CRITICAL'

        summary = 'Cloudtrail Logging Disabled: ' + event['_source']['requestParameters']['name']

        return self.createAlertDict(summary, category, tags, [event], severity)
