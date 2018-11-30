#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
# Copyright (c) 2014 Mozilla Corporation


from lib.alerttask import AlertTask
from mozdef_util.query_models import SearchQuery, PhraseMatch, TermsMatch, QueryStringMatch
import requests
import json
import logging

logger = logging.getLogger()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

class AlertWatchList(AlertTask):
    def main(self):
        self.parse_config('get_watchlist.conf', ['api_url'])

        #Connect to rest api and grab response
        r = requests.get(self.config.api_url)
        status = r.status_code
        index = 0
        if status == 200:
            status = r.status_code
            response = r.text
            terms_list = json.loads(response)
            while index < len(terms_list):
                term = terms_list[index]
                term = '"{}"'.format(term)
                index += 1

                # Create a query to look back the last 20 minutes
                search_query = SearchQuery(minutes=20)
                content = QueryStringMatch(str(term))
                search_query.add_must(content)
                self.filtersManual(search_query)
                self.searchEventsSimple()
                self.walkEvents()

    # Set alert properties
    def onEvent(self, event):
        category = 'watchlist'
        tags = ['watchtarget']
        severity = 'WARNING'

        ev = event['_source']

        # If the event severity is below what we want, just ignore
        # the event.
        if 'details' not in ev:
            return None
        if 'details' in ev:
            if 'sourceipaddress' in ev['details']:
                sourceipaddress = ev['details']['sourceipaddress']
                print sourceipaddress
            if 'username' in ev['details'] or 'originaluser' in ev['details']:
                user = ev['details']['username']
            if 'hostname' in ev:
                hostname = ev['hostname']
            else:
                return None

        summary = 'Watchlist term detected by {} from {} on {}'.format(user, sourceipaddress, hostname)
        return self.createAlertDict(summary, category, tags, [event], severity)
