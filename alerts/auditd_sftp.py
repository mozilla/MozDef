#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# Copyright (c) 2014 Mozilla Corporation

from lib.alerttask import AlertTask
from mozdef_util.query_models import SearchQuery, TermMatch, PhraseMatch


class AlertSFTPEvent(AlertTask):
    def main(self):
        search_query = SearchQuery(minutes=5)

        search_query.add_must([
            TermMatch('category', 'execve'),
            TermMatch('processname', 'audisp-json'),
            TermMatch('details.processname', 'ssh'),
            PhraseMatch('details.parentprocess', 'sftp')
        ])

        self.filtersManual(search_query)
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
        if 'hostname' in x:
            srchost = x['hostname']
        if 'details' in x:
            if 'originaluser' in x['details']:
                username = x['details']['originaluser']
            if 'cwd' in x['details']:
                directory = x['details']['cwd']

        summary = 'SFTP Event by {0} from host {1} in directory {2}'.format(username, srchost, directory)

        # Create the alert object based on these properties
        return self.createAlertDict(summary, category, tags, [event], severity)
