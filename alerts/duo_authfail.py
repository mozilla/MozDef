# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# Copyright (c) 2017 Mozilla Corporation

from lib.alerttask import AlertTask
from mozdef_util.query_models import SearchQuery, TermMatch, ExistsMatch, PhraseMatch


class AlertDuoAuthFail(AlertTask):
    def main(self):
        self.parse_config('duo_authfail.conf', ['url'])
        search_query = SearchQuery(minutes=15)

        search_query.add_must([
            TermMatch('category', 'authentication'),
            ExistsMatch('details.sourceipaddress'),
            ExistsMatch('details.username'),
            PhraseMatch('details.result', 'fraud')
        ])

        self.filtersManual(search_query)
        self.searchEventsSimple()
        self.walkEvents()

    # Set alert properties
    def onEvent(self, event):
        category = 'duosecurity'
        tags = ['duosecurity', 'duosecurity_auth_fail']
        severity = 'WARNING'
        url = self.config.url

        sourceipaddress = 'unknown'
        user = 'unknown'
        x = event['_source']
        if 'details' in x:
            if 'sourceipaddress' in x['details']:
                sourceipaddress = x['details']['sourceipaddress']
            if 'username' in x['details']:
                user = x['details']['username']

        summary = 'Duo Authentication Failure: user {1} rejected and marked a Duo Authentication attempt from {0} as fraud'.format(sourceipaddress, user)

        # Create the alert object based on these properties
        return self.createAlertDict(summary, category, tags, [event], severity, url)
