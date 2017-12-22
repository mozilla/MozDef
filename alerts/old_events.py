#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
# Copyright (c) 2017 Mozilla Corporation
#

from lib.alerttask import AlertTask
from query_models import SearchQuery, LessThanMatch

from datetime import datetime, timedelta
from utilities.toUTC import toUTC


class OldEvents(AlertTask):

    def main(self):
        search_query = SearchQuery(hours=6)

        day_old_date = toUTC(datetime.now() - timedelta(days=1)).isoformat()
        search_query.add_must(LessThanMatch('utctimestamp', day_old_date))
        self.filtersManual(search_query)

        self.searchEventsAggregated('mozdefhostname', samplesLimit=1000)
        self.walkAggregations(threshold=1)

    def onAggregation(self, aggreg):
        category = 'maitenance'
        tags = ['pipeline']
        severity = 'ERROR'

        summary = 'Events have an outdated utctimestamp ({0})'.format(aggreg['count'])
        return self.createAlertDict(summary, category, tags, aggreg['events'], severity)
