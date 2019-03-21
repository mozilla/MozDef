# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
# Copyright (c) 2014 Mozilla Corporation

import os
from configlib import getConfig, OptionParser
import sys
from datetime import datetime, timedelta
sys.path.append(os.path.join(os.path.dirname(__file__), "../lib"))
from iqrlib import iqr


class message(object):
    def __init__(self):
        '''
        takes an incoming alert
        and uses it to trigger an event using
        the pager duty event api
        '''

        # set my own conf file
        # relative path to the rest index.py file
        self.configfile = os.path.join(os.path.dirname(__file__), 'iqrisk.conf')
        self.options = None
        if os.path.exists(self.configfile):
            self.initConfiguration()

        self.registration = self.options.keywords.split(" ")
        self.priority = 150

        self.timeformats = {}
        self.timeformats['ips'] = 'last_seen'
        self.timeformats['domains'] = 'last_seen'
        self.timeformats['nameservers'] = 'last_seen'
        self.timeformats['events'] = 'date'

    def initConfiguration(self):
        myparser = OptionParser()
        # setup self.options by sending empty list [] to parse_args
        (self.options, args) = myparser.parse_args([])

        # fill self.options with plugin-specific options
        self.options.keywords = getConfig('keywords', 'localhost', self.configfile)
        self.options.apiurl = getConfig('apiurl', 'APIURLHERE', self.configfile)
        self.options.apikey = getConfig('apikey', 'APIKEYHERE', self.configfile)
        self.options.allowedipreptypes = getConfig('allowedipreptypes', 'DEFAULTS', self.configfile).split(',')
        self.options.alloweddomainreptypes = getConfig('alloweddomainreptypes', 'DEFAULTS', self.configfile).split(',')

    def onMessage(self, message):
        # here is where you do something with the incoming alert message
        dtnow = datetime.today()
        dt30 = dtnow - timedelta(days=30)
        if 'sourceipaddress' in message['details']:
            rep = iqr(message['details']['sourceipaddress'], self.options)
            message['intel'] = {}
            # events get a special treatment to only get the most recent ones
            rep.get_reputation('events', "ip")
            message['intel']['idsevents'] = list()
            for entry in rep.reputation['events']:
                dtioc = datetime.strptime(entry[self.timeformats['events']], '%Y-%m-%d')
                if dtioc > dt30:
                    message['intel']['idsevents'].append(entry)
            # the list of most recent domains
            rep.get_reputation('domains', "ip")
            message['intel']['domains'] = list()
            for entry in rep.reputation['domains']:
                dtioc = datetime.strptime(entry[self.timeformats['domains']], '%Y-%m-%d')
                if dtioc > dt30:
                    message['intel']['domains'].append(entry)
            # generic reputation info
            rep.get_reputation('reputation', "ip")
            message['intel']['reputation'] = rep.reputation['reputation']
        if 'destinationfqdn' in message['details']:
            rep = iqr(message['details']['destinationfqdn'], self.options)
            message['intel'] = {}
            # generic reputation info
            rep.get_reputation('reputation', "domain")
            message['intel']['reputation'] = rep.reputation['reputation']
        if 'reputation' in message['intel']:
            message['tags'].append('intel')
        # you can modify the message if needed
        # plugins registered with lower (>2) priority
        # will receive the message and can also act on it
        # but even if not modified, you must return it
        return message
