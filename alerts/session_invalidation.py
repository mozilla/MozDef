#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# Copyright (c) 2017 Mozilla Corporation

from lib.alerttask import AlertTask
from mozdef_util.query_models import SearchQuery, TermMatch


class AlertSessionInvalidation(AlertTask):
    '''An alert that fires whenever the Session Invalidation application
    is invoked to terminate a user's sessions.

    See https://github.com/mozilla/session-invalidation/
    '''

    def main(self):
        query = SearchQuery(minutes=15)

        # Search for events from the session invalidation app wherein
        # an authenticated user terminated a user's sessions.
        query.add_must([
            TermMatch('category', 'sessioninvalidation'),
        ])

        self.filtersManual(query)
        self.searchEventsAggregated('details.actor', samplesLimit=1000)
        self.walkAggregations(threshold=1, config=None)

    def onAggregation(self, agg):
        category = 'sessioninvalidation'
        tags = ['sessioninvalidation']
        severity = 'WARNING'

        actor = agg['value']
        events = agg['events']

        terminations = [
            {
                'invalidateduser': event['details']['invalidateduser'],
                'invalidatedsessions': event['details']['invalidatedsessions'],
            }
            for event in [evt['_source'] for evt in events]
            if event.get('details', {}).get('invalidateduser') is not None
        ]

        if len(terminations) == 0:
            return None

        affected_users = [
            t['invalidateduser']
            for t in terminations
        ]

        summary = '{0} terminated sessions for user(s) {1}'.format(
            actor,
            ', '.join(affected_users),
        )

        alert = self.createAlertDict(
            summary,
            category,
            tags,
            events,
            severity=severity,
        )

        details = alert.get('details', {})

        details.update({
            'actor': actor,
            'username': actor,
            'terminations': terminations,
        })

        alert['details'] = details

        return alert
