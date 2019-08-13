#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# Copyright (c) 2017 Mozilla Corporation


from lib.deadman_alerttask import DeadmanAlertTask
from mozdef_util.query_models import SearchQuery, TermMatch


class AlertCloudtrailDeadman(DeadmanAlertTask):
    def main(self):
        search_query = SearchQuery(hours=1)

        search_query.add_must([
            TermMatch('source', 'cloudtrail')
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
