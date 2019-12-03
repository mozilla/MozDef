# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# Copyright (c) 2014 Mozilla Corporation

import requests
import json
import os
from configlib import getConfig, OptionParser


class message(object):
    def __init__(self):
        '''
        takes an incoming alert
        and uses it to trigger an event using
        the pager duty event api
        '''

        # set my own conf file
        # relative path to the rest index.py file
        self.configfile = os.path.join(os.path.dirname(__file__), 'pagerDutyTriggerEvent.conf')
        self.options = None
        if os.path.exists(self.configfile):
            self.initConfiguration()

        self.registration = self.options.keywords.split(" ")
        self.priority = 1

    def initConfiguration(self):
        myparser = OptionParser()
        # setup self.options by sending empty list [] to parse_args
        (self.options, args) = myparser.parse_args([])

        # fill self.options with plugin-specific options
        # change this to your default zone for when it's not specified
        self.options.serviceKey = getConfig('serviceKey', 'APIKEYHERE', self.configfile)
        self.options.keywords = getConfig('keywords', 'KEYWORDS', self.configfile)
        self.options.clienturl = getConfig('clienturl', 'CLIENTURL', self.configfile)
        try:
            self.options.docs = json.loads(getConfig('docs', {}, self.configfile))
        except:
            self.options.docs = {}

    def onMessage(self, alert):
        # As of Dec. 3, 2019, alert actions are given entire alerts rather
        # than just their source
        message = alert['_source']

        # here is where you do something with the incoming alert message
        doclink = 'unknown'
        if message['category'] in self.options.docs:
            doclink = self.options.docs[message['category']]
        if 'summary' in message:
            headers = {
                'Content-type': 'application/json',
            }
            payload = json.dumps({
                "service_key": "{0}".format(self.options.serviceKey),
                "event_type": "trigger",
                "description": "{0}".format(message['summary']),
                "client": "MozDef",
                "client_url": "https://" + self.options.clienturl + "/{0}".format(message['events'][0]['documentsource']['alerts'][0]['id']),
                "contexts": [
                    {
                        "type": "link",
                        "href": "https://" + "{0}".format(doclink),
                        "text": "View runbook on mana"
                    }
                ]
            })
            requests.post(
                'https://events.pagerduty.com/generic/2010-04-15/create_event.json',
                headers=headers,
                data=payload,
            )
        # you can modify the message if needed
        # plugins registered with lower (>2) priority
        # will receive the message and can also act on it
        # but even if not modified, you must return it
        return message
