#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
# Copyright (c) 2016 Mozilla Corporation
#
# Contributors:
# Brandon Myers bmyers@mozilla.com

from lib.alerttask import AlertTask
from query_models import SearchQuery, TermMatch


class AlertCloudtrailDeleteBucket(AlertTask):
    def main(self):
        search_query = SearchQuery(minutes=30)

        search_query.add_must([
            TermMatch('_type', 'cloudtrail'),
            TermMatch('eventName', 'DeleteBucket'),
        ])

        self.filtersManual(search_query)
        self.searchEventsSimple()
        self.walkEvents()

    def onEvent(self, event):
        category = 'AWSCloudtrail'
        tags = ['cloudtrail', 'aws']
        severity = 'ERROR'

        bucket_name = event['_source']['requestParameters']['bucketName']

        summary = "S3 Bucket (" + bucket_name + ") deleted"

        return self.createAlertDict(summary, category, tags, [event], severity)