#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
# Copyright (c) 2014 Mozilla Corporation


import requests
import json

from lib.alerttask import AlertTask
from requests_jwt import JWTAuth
from mozdef_util.utilities.logger import logger
from mozdef_util.query_models import SearchQuery, QueryStringMatch


class AlertWatchList(AlertTask):
    def main(self):
        self.parse_config('get_watchlist.conf', ['api_url', 'jwt_secret'])

        jwt_token = JWTAuth(self.config.jwt_secret)
        jwt_token.set_header_format('Bearer %s')

        # Connect to rest api and grab response
        r = requests.get(self.config.api_url, auth=jwt_token)
        status = r.status_code
        index = 0
        if status == 200:
            status = r.status_code
            response = r.text
            terms_list = json.loads(response)
            while index < len(terms_list):
                term = terms_list[index]
                term = '"{}"'.format(term)
                self.watchterm = term
                index += 1
                self.process_alert(term)
        else:
            logger.error('The watchlist request failed. Status {0}.\n'.format(status))

    def process_alert(self, term):
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
        user = ''
        sourceipaddress = ''
        hostname = ''
        source_data = ''
        user_data = ''

        # If the event severity is below what we want, just ignore
        # the event.
        if 'details' not in ev:
            return None
        if 'details' in ev:
            if 'sourceipaddress' in ev['details']:
                sourceipaddress = ev['details']['sourceipaddress']
                source_data = 'from {}'.format(sourceipaddress)
            if 'username' in ev['details'] or 'originaluser' in ev['details'] or 'user' in ev['details']:
                if 'username' in ev['details']:
                    user = ev['details']['username']
                    user_data = 'by {}'.format(user)
                elif 'originaluser' in ev['details']:
                    user = ev['details']['originaluser']
                    user_data = 'by {}'.format(user)
                elif 'user' in ev['details']:
                    user = ev['details']['user']
                    user_data = 'by {}'.format(user)
            if 'hostname' in ev:
                hostname = ev['hostname']
            else:
                return None

        summary = 'Watchlist term {} detected {} {} on {}'.format(self.watchterm, user_data, source_data, hostname)
        return self.createAlertDict(summary, category, tags, [event], severity)
