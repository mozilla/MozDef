#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# Copyright (c) 2015 Mozilla Corporation

from lib.alerttask import AlertTask
from mozdef_util.query_models import SearchQuery, TermMatch


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
        category = 'user_feedback'
        tags = ['user_feedback']
        severity = 'NOTICE'

        user = event['_source']['details']['alert_information']['user_id']
        event_summary = event['_source']['summary']
        event_date = event['_source']['details']['alert_information']['date']
        summary = "{} escalated alert within single-sign on (SSO) dashboard. Event Date: {} Summary: \"{}\"".format(user, event_date, event_summary)

        for alert_code, tag in self._config.items():
            if event['_source']['details']['alert_information']['alert_code'] == alert_code:
                tags.append(tag)

        return self.createAlertDict(summary, category, tags, [event], severity)
