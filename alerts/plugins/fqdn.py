# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
# Copyright (c) 2014 Mozilla Corporation

from configlib import getConfig, OptionParser
import netaddr
import sys
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

        #self.registration = self.options.keywords.split(" ")
        self.registration = ['squid']
        self.priority = 2
    
    def onMessage(self, message):
        '''
        Extracts the subdomain, and the domain name and merges them into FQDN
        '''

        # here is where you do something with the incoming alert message
        if 'events' in message.keys():
            if 'details' not in message:
                message['details'] = {}
            if 'documentsource' in message['events'][0].keys():
                if 'details' in message['events'][0]['documentsource'].keys():
                    event = message['events'][0]['documentsource']['details']
                if message['category'] == 'squid':
                    if 'squid' in message['events'][0]['documentsource']['tags']:
                        if 'destination' in event.keys():
                            fqdn = addFQDN(event['destination'])
                            if fqdn is not None:
                                message['details']['destinationfqdn'] = fqdn

        # you can modify the message if needed
        # plugins registered with lower (>2) priority
        # will receive the message and can also act on it
        # but even if not modified, you must return it
        return message
