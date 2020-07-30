#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# Copyright (c) 2017 Mozilla Corporation

from lib.alerttask import AlertTask
from mozdef_util.query_models import SearchQuery, TermMatch, ExistsMatch


class AlertTriageBotEscalation(AlertTask):
    def main(self):
        self.parse_config('triagebot_escalation.conf', ['url', 'severity'])

        search_query = SearchQuery(minutes=15)

        search_query.add_must([
            TermMatch('category', 'triagebot'),
            TermMatch('details.userresponse', 'no'),
            ExistsMatch('details.email'),
            ExistsMatch('details.identifier')
        ])

        self.filtersManual(search_query)

        # Search events
        self.searchEventsSimple()
        self.walkEvents()

    # Set alert properties
    def onEvent(self, event):
        msg = event['_source']
        category = 'access'
        tags = ['triagebot_escalation']
        severity = self.config.severity
        url = self.config.url

        # the summary of the alert is the same as the event
        summary = "TriageBot Escalation for event: {0} sent to PagerDuty per 'NO' response from User: {1}".format(msg['details']['identifier'], msg['details']['email'])

        # Create the alert object based on these properties
        return self.createAlertDict(summary, category, tags, [event], severity, url)
