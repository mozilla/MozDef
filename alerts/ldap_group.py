#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
# Copyright (c) 2014 Mozilla Corporation
#
# Contributors:
# Jeff Bryner jbryner@mozilla.com

from lib.alerttask import AlertTask
from query_models import SearchQuery, TermMatch, PhraseMatch


class ldapGroupModify(AlertTask):
    def main(self):
        search_query = SearchQuery(minutes=15)

        search_query.add_must([
            TermMatch('category', 'ldapChange'),
            TermMatch('details.changetype', 'modify'),
            PhraseMatch("summary", "groups")
        ])

        self.filtersManual(search_query)
        # Search events
        self.searchEventsSimple()
        self.walkEvents()

    # Set alert properties
    def onEvent(self, event):
        category = 'ldap'
        tags = ['ldap']
        severity = 'INFO'
        summary = '{0}'.format(event['_source']['summary'])

        # Create the alert object based on these properties
        return self.createAlertDict(summary, category, tags, [event], severity)
