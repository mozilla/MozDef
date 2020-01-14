#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# Copyright (c) 2017 Mozilla Corporation

import logging
import sys
from lib.alerttask import AlertTask
from mozdef_util.query_models import SearchQuery


logger = logging.getLogger(__name__)


def setup_logging():
    logger = logging.getLogger()
    logging.StreamHandler(sys.stdout)
    logger.setLevel(logging.DEBUG)
    return logger


class AlertCloudtrailLoggingDisabled(AlertTask):
    def _configureKombu(self):
        """Override the normal behavior of this in order to run in lambda."""
        pass

    def alertToMessageQueue(self, alertDict):
        """Override the normal behavior of this in order to run in lambda."""
        pass

    def main(self):
        # How many minutes back in time would you like to search?
        search_query = SearchQuery(minutes=15)

        # What would you like to search for?
        # search_query.add_must([
        #    TermMatch('source', 'cloudtrail'),
        #    TermMatch('details.eventname', 'DescribeTable')
        # ])

        self.filtersManual(search_query)
        self.searchEventsSimple()
        self.walkEvents()

    def onEvent(self, event):
        category = 'AWSCloudtrail'

        # Useful tag and severity rankings for your alert.
        tags = ['cloudtrail', 'aws', 'cloudtrailpagerduty']
        severity = 'CRITICAL'

        # What message should surface in the user interface when this fires?
        summary = 'The alert fired!'

        return self.createAlertDict(summary, category, tags, [event], severity)

        # Learn more about MozDef alerts by exploring the "Alert class!"


def handle(event, context):
    logger = setup_logging()
    logger.debug('Function initialized.')
    a = AlertCloudtrailLoggingDisabled()
    return a.main()
