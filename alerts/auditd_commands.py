#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# Copyright (c) 2017 Mozilla Corporation

from lib.alerttask import AlertTask
from mozdef_util.query_models import SearchQuery, TermMatch


class AlertAuditdCommands(AlertTask):
    def main(self):
        self.parse_config('auditd_commands.conf', ['commands'])
        search_query = SearchQuery(minutes=30)

        auditd_match = TermMatch('category', 'auditd')
        auditd_match |= TermMatch('category', 'execve')
        search_query.add_must(auditd_match)

        command_names_matcher = None
        for name in self.config.commands.split(","):
            if command_names_matcher is None:
                command_names_matcher = TermMatch('details.processname', name)
            else:
                command_names_matcher |= TermMatch('details.processname', name)

        search_query.add_must(command_names_matcher)

        self.filtersManual(search_query)
        self.searchEventsSimple()
        self.walkEvents()

    def onEvent(self, event):
        category = 'auditd'
        tags = ['auditd_command']
        severity = 'WARNING'

        user = event['_source']['details']['originaluser']
        host = event['_source']['hostname']
        command = event['_source']['details']['processname']
        summary = "{user} on {host} executed {command}".format(
            user=user,
            host=host,
            command=command
        )

        return self.createAlertDict(summary, category, tags, [event], severity)
