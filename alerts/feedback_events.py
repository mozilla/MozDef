#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
# Copyright (c) 2015 Mozilla Corporation

from lib.alerttask import AlertTask
from query_models import SearchQuery, TermMatch


class AlertFeedbackEvents(AlertTask):
    def main(self):
        self._config = self.parse_json_alert_config('feedback_events.json')
        search_query = SearchQuery(minutes=30)

        search_query.add_must([
            TermMatch('category', 'user_feedback'),
            TermMatch('details.action', 'escalate')
        ])

        self.filtersManual(search_query)
        self.searchEventsSimple()
        self.walkEvents()

    def onEvent(self, event):
        category = 'feedback'
        tags = ['feedback']
        severity = 'NOTICE'
        summary = 'SSO Escalate Event Received'

        for category, tag in self._config.iteritems():
            if event['_source']['details']['alert_information']['category'] == category:
                tags.append(tag)

        return self.createAlertDict(summary, category, tags, [event], severity)
