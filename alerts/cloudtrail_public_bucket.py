#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# Copyright (c) 2014 Mozilla Corporation


from lib.alerttask import AlertTask
from mozdef_util.query_models import SearchQuery, TermMatch


class AlertCloudtrailPublicBucket(AlertTask):
    def main(self):
        search_query = SearchQuery(minutes=20)

        search_query.add_must([
            TermMatch('source', 'cloudtrail'),
            TermMatch('details.eventname', 'CreateBucket'),
            TermMatch('details.requestparameters.x-amz-acl', 'public-read-write'),
        ])

        self.filtersManual(search_query)
        self.searchEventsSimple()
        self.walkEvents()

    # Set alert properties
    def onEvent(self, event):
        request_parameters = event['_source']['details']['requestparameters']
        category = 'access'
        tags = ['cloudtrail']
        severity = 'INFO'

        bucket_name = 'Unknown'
        if 'bucketname' in request_parameters:
            bucket_name = request_parameters['bucketname']

        summary = "The s3 bucket {0} is listed as public".format(bucket_name)
        return self.createAlertDict(summary, category, tags, [event], severity)
