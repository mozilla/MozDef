#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
# Copyright (c) 2014 Mozilla Corporation
#
# Contributors:
# Anthony Verez averez@mozilla.com
# Jeff Bryner jbryner@mozilla.com
# Aaron Meihm ameihm@mozilla.com
# Michal Purzynski <mpurzynski@mozilla.com>
# Alicia Smith <asmith@mozilla.com>

from lib.alerttask import AlertTask
import pyes

class AlertSFTPEvent(AlertTask):
    def main(self):
        # look for events in last X mins
        date_timedelta = dict(minutes=5)
        # Configure filters using pyes
        must = [
            pyes.TermFilter('_type', 'auditd'),
            pyes.TermFilter('category', 'execve'),
            pyes.TermFilter('processname', 'audisp-json'),
            pyes.TermFilter('details.processname', 'ssh'),
            pyes.QueryFilter(pyes.MatchQuery('details.parentprocess', 'sftp', 'phrase')),
        ]
        self.filtersManual(date_timedelta, must=must)
        self.searchEventsSimple()
        self.walkEvents()

    # Set alert properties
    def onEvent(self, event):
        category = 'execve'
        severity = 'NOTICE'
        tags = ['audisp-json, audit']

        srchost = 'unknown'
        username = 'unknown'
        directory = 'unknown'
        x = event['_source']
        if 'details' in x:
            if 'hostname' in x['details']:
                srchost = x['details']['hostname']
            if 'originaluser' in x['details']:
                username = x['details']['originaluser']
            if 'cwd' in x['details']:
                directory = x['details']['cwd']

        summary = 'SFTP Event by {0} from host {1} in directory {2}'.format(username, srchost, directory)

        # Create the alert object based on these properties
        return self.createAlertDict(summary, category, tags, [event], severity)
