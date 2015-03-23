# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
# Copyright (c) 2014 Mozilla Corporation
#
# Contributors:
# Jeff Bryner jbryner@mozilla.com

import requests
import json
import os
import sys
from configlib import getConfig, OptionParser


class message(object):
    def __init__(self):
        '''
        takes an incoming alert
        and uses it to trigger an event using
        the pager duty event api
        '''
    
        self.registration = ['bro']
        self.priority = 2

        # set my own conf file
        # relative path to the rest index.py file
        self.configfile = './plugins/pagerDutyTriggerEvent.conf'
        self.options = None
        if os.path.exists(self.configfile):
            sys.stdout.write('found conf file {0}\n'.format(self.configfile))
            self.initConfiguration()
                
    def initConfiguration(self):
        myparser = OptionParser()
        # setup self.options by sending empty list [] to parse_args
        (self.options, args) = myparser.parse_args([])
        
        # fill self.options with plugin-specific options
        # change this to your default zone for when it's not specified
        self.options.serviceKey = getConfig('serviceKey', 'APIKEYHERE', self.configfile)
        

    def onMessage(self, message):
        # here is where you do something with the incoming alert message
        if 'summary' in message.keys() :
            print message['summary']

            headers = {
                'Content-type': 'application/json',
            }
            payload = json.dumps({
              "service_key": "{0}".format(self.options.serviceKey),
              "incident_key": "bro",
              "event_type": "trigger",
              "description": "{0}".format(message['summary']),
              "client": "mozdef",
              "client_url": "http://mozdef.rocks",
              "details": message['events']
            })
            r = requests.post(
                            'https://events.pagerduty.com/generic/2010-04-15/create_event.json',
                            headers=headers,
                            data=payload,
            )
            print r.status_code
            print r.text        
        # you can modify the message if needed
        # plugins registered with lower (>2) priority
        # will receive the message and can also act on it
        # but even if not modified, you must return it
        return message