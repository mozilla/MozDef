#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
# Copyright (c) 2017 Mozilla Corporation
#
# Contributors:
# Brandon Myers bmyers@mozilla.com


from lib.alerttask import AlertTask
from query_models import SearchQuery, TermMatch


class AlertCloudtrailDeadman(AlertTask):
    def main(self):
        search_query = SearchQuery(hours=1)

        search_query.add_must([
            TermMatch('_type', 'cloudtrail'),
        ])

        self.filtersManual(search_query)
        self.searchEventsSimple()
        self.walkEvents()

    # Set alert properties
    # if no events found
    def onNoEvent(self):
        category = 'deadman'
        tags = ['cloudtrail', 'aws']
        severity = 'ERROR'

        summary = 'No cloudtrail events found the last hour'

        # Create the alert object based on these properties
        return self.createAlertDict(summary, category, tags, [], severity=severity)
