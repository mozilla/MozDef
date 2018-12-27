# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
# Copyright (c) 2014 Mozilla Corporation

from configlib import getConfig, OptionParser
import netaddr
import os


def isIPv4(ip):
    try:
        return netaddr.valid_ipv4(ip)
    except:
        return False


def isIPv6(ip):
    try:
        return netaddr.valid_ipv6(ip)
    except:
        return False


def addError(message, error):
    '''add an error note to a message'''
    if 'errors' not in message.keys():
        message['errors'] = list()
    if isinstance(message['errors'], list):
        message['errors'].append(error)


class message(object):
    def __init__(self):
        '''
        takes an incoming alert
        and uses it to trigger an event using
        the pager duty event api
        '''

        # set my own conf file
        # relative path to the rest index.py file
        self.configfile = os.path.join(os.path.dirname(__file__), 'ipaddr.conf')
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
        self.options.keywords = getConfig('keywords', 'localhost', self.configfile)

    def onMessage(self, message):
        '''
        Examine possible ip addresses for the following:
          ipv6 in an ipv4 field
          ipv4 in another field
          '-' or other invalid ip in the ip field
        Also sets ipv4 in two fields:
            ipaddress (decimal mapping IP)
            ipv4address (string mapping)
            Elastic search is inconsistent about returning IPs as
            decimal or IPs.
            In a query an IP field is returned as string.
            In a facets an IP field is returned as decimal.
            No ES field type exists for ipv6, so always having
            a string version is the most flexible option.
        '''

        # here is where you do something with the incoming alert message
        if 'events' in message.keys():
            if 'documentsource' in message['events'][0].keys():
                if 'details' in message['events'][0]['documentsource'].keys():
                    event = message['events'][0]['documentsource']['details']
                    if 'details' not in message:
                        message['details'] = {}
                    # forwarded header can be spoofed, so try it first,
                    # but override later if we've a better field.
                    if 'http_x_forwarded_for' in event.keys():
                        # should be a comma delimited list of ips with the original client listed first
                        ipText = event['http_x_forwarded_for'].split(',')[0]
                        if isIPv4(ipText) and 'sourceipaddress' not in event.keys():
                            message['details']['sourceipaddress'] = ipText
                        if isIPv4(ipText) and 'sourceipv4address' not in event.keys():
                            message['details']['sourceipv4address'] = ipText
                        if isIPv6(ipText) and 'sourceipv6address' not in event.keys():
                            message['details']['sourceipv6address'] = ipText

                    if 'sourceipaddress' in event.keys():
                        ipText = event['sourceipaddress']
                        if isIPv6(ipText):
                            event['sourceipv6address'] = ipText
                            message['details']['sourceipaddress'] = '0.0.0.0'
                            addError(message, 'plugin: {0} error: {1}'.format('ipFixUp.py', 'sourceipaddress is ipv6, moved'))
                        elif isIPv4(ipText):
                            message['details']['sourceipv4address'] = ipText
                            message['details']['sourceipaddress'] = ipText
                        else:
                            # Smells like a hostname, let's save it as source field
                            message['details']['source'] = event['sourceipaddress']
                            message['details']['sourceipaddress'] = None

                    if 'destinationipaddress' in event.keys():
                        ipText = event['destinationipaddress']
                        if isIPv6(ipText):
                            message['details']['destinationipv6address'] = ipText
                            message['details']['destinationipaddress'] = '0.0.0.0'
                            addError(message, 'plugin: {0} error: {1}'.format('ipFixUp.py', 'destinationipaddress is ipv6, moved'))
                        elif isIPv4(ipText):
                            message['details']['destinationipv4address'] = ipText
                            message['details']['destinationipaddress'] = ipText
                        else:
                            # Smells like a hostname, let's save it as destination field
                            message['details']['destination'] = event['destinationipaddress']
                            message['details']['destinationipaddress'] = None

                    if 'cluster_client_ip' in event.keys():
                        ipText = event['cluster_client_ip']
                        if isIPv4(ipText):
                            message['details']['sourceipaddress'] = ipText

        # you can modify the message if needed
        # plugins registered with lower (>2) priority
        # will receive the message and can also act on it
        # but even if not modified, you must return it
        return message
