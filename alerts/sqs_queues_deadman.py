#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
# Copyright (c) 2017 Mozilla Corporation
#
# Contributors:
# bmyers@mozilla.com

from lib.alerttask import AlertTask
from query_models import SearchQuery, TermMatch
from configlib import getConfig, OptionParser


class AlertSQSQueuesDeadman(AlertTask):

    def main(self):
        self.config_file = './sqs_queues_deadman.conf'
        self.initConfiguration()
        for queue_name in self.config.sqs_queues:
            self.sqs_queue_name = queue_name
            self.process_alert()

    def initConfiguration(self):
        myparser = OptionParser()
        (self.config, args) = myparser.parse_args([])
        sqs_queues_str = getConfig('sqs_queues', '', self.config_file)
        self.config.sqs_queues = sqs_queues_str.split(',')

    def process_alert(self):
        search_query = SearchQuery(hours=1)
        search_query.add_must(TermMatch('tags', self.sqs_queue_name))
        self.filtersManual(search_query)
        self.searchEventsSimple()
        self.walkEvents()

    def onNoEvent(self):
        category = 'deadman'
        tags = [self.sqs_queue_name, 'sqs']
        severity = 'ERROR'

        summary = 'No events found from {} sqs queue the last hour'.format(self.sqs_queue_name)

        # Create the alert object based on these properties
        return self.createAlertDict(summary, category, tags, [], severity=severity)
