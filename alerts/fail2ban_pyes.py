#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
# Copyright (c) 2014 Mozilla Corporation
#
# Contributors:
# Anthony Verez averez@mozilla.com

from lib.alerttask import AlertTask
from query_models import SearchQuery, TermMatch, QueryFilter, MatchQuery


class AlertFail2ban(AlertTask):
    def main(self):
        search_query = SearchQuery(minutes=10)

        search_query.add_must([
            TermMatch('_type', 'event'),
            TermMatch('program', 'fail2ban'),
            QueryFilter(MatchQuery("summary","banned for","phrase"))
        ])

        self.filtersManual(search_query)

        # Search events
        self.searchEventsSimple()
        self.walkEvents()

    # Set alert properties
    def onEvent(self, event):
        category = 'fail2ban'
        tags = ['fail2ban']
        severity = 'NOTICE'

        summary='{0}: {1}'.format(event['_source']['details']['hostname'], event['_source']['summary'].strip())

        # Create the alert object based on these properties
        return self.createAlertDict(summary, category, tags, [event], severity)
