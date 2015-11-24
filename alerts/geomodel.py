#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
# Copyright (c) 2015 Mozilla Corporation
#
# Contributors:
# Aaron Meihm <ameihm@mozilla.com>

from lib.alerttask import AlertTask
import pyes

class AlertGeomodel(AlertTask):
    def main(self):
        date_timedelta = dict(minutes=30)

        must = [
            pyes.TermFilter('_type', 'event'),
            pyes.TermFilter('category', 'geomodelnotice'),
        ]
        self.filtersManual(date_timedelta, must=must, must_not=[])
        self.searchEventsSimple()
        self.walkEvents()

    # Set alert properties
    def onEvent(self, event):
        category = 'geomodel'
        tags = ['geomodel']
        severity = 'NOTICE'

        summary = event['_source']['summary']
        return self.createAlertDict(summary, category, tags, [event], severity)
