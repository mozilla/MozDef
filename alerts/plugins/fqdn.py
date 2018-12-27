# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
# Copyright (c) 2014 Mozilla Corporation

from configlib import getConfig, OptionParser
import os
import tldextract


def addFQDN(host):
    fqdn = tldextract.extract(host)

    fqdn = '.'.join(part for part in fqdn if part)

    return fqdn


class message(object):
    def __init__(self):
        '''
        takes an incoming alert
        and uses it to trigger an event using
        the pager duty event api
        '''

        # set my own conf file
        # relative path to the rest index.py file
        self.configfile = os.path.join(os.path.dirname(__file__), 'fqdn.conf')
        self.options = None
        if os.path.exists(self.configfile):
            self.initConfiguration()

        self.registration = self.options.keywords.split(" ")
        self.priority = 2

    def initConfiguration(self):
        myparser = OptionParser()
        # setup self.options by sending empty list [] to parse_args
        (self.options, args) = myparser.parse_args([])

        # fill self.options with plugin-specific options
        self.options.keywords = getConfig('keywords', 'localhost', self.configfile)

    def onMessage(self, message):
        '''
        Extracts the subdomain, and the domain name and merges them into FQDN
        '''

        # here is where you do something with the incoming alert message
        if 'events' in message.keys():
            if 'documentsource' in message['events'][0].keys():
                if 'details' in message['events'][0]['documentsource'].keys():
                    event = message['events'][0]['documentsource']['details']
            if 'details' not in message:
                message['details'] = {}
            if 'destination' in event.keys():
                fqdn = addFQDN(event['destination'])
                if fqdn is not None:
                    message['details']['destinationfqdn'] = fqdn

        # you can modify the message if needed
        # plugins registered with lower (>2) priority
        # will receive the message and can also act on it
        # but even if not modified, you must return it
        return message