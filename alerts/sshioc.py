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

class AlertSSHIOC(AlertTask):
    def main(self):
        date_timedelta = dict(minutes=30)

        must = [
            pyes.TermFilter('_type', 'event'),
            pyes.TermFilter('tags', 'mig-runner-sshioc'),
        ]
        self.filtersManual(date_timedelta, must=must, must_not=[])
        self.searchEventsSimple()
        self.walkEvents()

    # Set alert properties
    def onEvent(self, event):
        category = 'sshioc'
        tags = ['sshioc']
        severity = 'WARNING'

        summary = 'SSH IOC match from runner plugin'
        return self.createAlertDict(summary, category, tags, [event], severity)
