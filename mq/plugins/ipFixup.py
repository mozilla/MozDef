# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
# Copyright (c) 2014 Mozilla Corporation
#
# Contributors:
# Jeff Bryner jbryner@mozilla.com

import netaddr


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
        '''register our criteria for being passed a message
           return a dict with fieldname:None to be sent anything with that field
           return a dict with fieldname:Value to be sent anything with that field/value
           return a string to be sent anything with any field matching that string evaluated as a regex.
           set the priority if you have a preference for order of plugins to run.
           0 goes first, 100 is assumed/default if not sent
        '''
        # ask for anything that could house an IP address
        rdict = dict()
        rdict['details'] = dict()
        rdict['details']['sourceipaddress'] = None
        rdict['details']['destinationipaddress'] = None
        rdict['details']['src'] = None
        rdict['details']['dst'] = None
        rdict['details']['srcip'] = None
        rdict['details']['dstip'] = None
        rdict['details']['http_x_forwarded_for'] = None
        self.registration = rdict
        self.priority = 15

    def onMessage(self, message):
        '''
        Examine possible ip addresses for the following:
          ipv6 in an ipv4 field
          ipv4 in another field
          '-' or other invalid ip in the ip field
        '''

        if 'details' in message.keys():
            # forwarded header can be spoofed, so try it first,
            # but override later if we've a better field.
            if 'http_x_forwarded_for' in message['details'].keys():
                # should be a comma delimited list of ips with the original client listed first
                ipText = message['details']['http_x_forwarded_for'].split(',')[0]
                if isIPv4(ipText) and 'sourceipaddress' not in message['details'].keys():
                    message['details']['sourceipaddress'] = ipText
                if isIPv6(ipText) and 'sourceipv6address' not in message['details'].keys():
                    message['details']['sourceipv6address'] = ipText

            if 'sourceipaddress' in message['details'].keys():
                ipText = message['details']['sourceipaddress']
                if isIPv6(ipText):
                    message['details']['sourceipv6address'] = ipText
                    message['details']['sourceipaddress'] = '0.0.0.0'
                    addError(message, 'plugin: {0} error: {1}'.format('ipFixUp.py', 'sourceipaddress is ipv6, moved'))
                elif not isIPv4(ipText):
                    if ipText == '-':
                        message['details']['sourceipaddress'] = '0.0.0.0'
                    else:
                        message['details']['sourceipaddress'] = '0.0.0.0'
                        addError(message, 'plugin: {0} error: {1}:{2}'.format('ipFixUp.py', 'sourceipaddress is invalid', ipText))

            if 'destinationipaddress' in message['details'].keys():
                ipText = message['details']['destinationipaddress']
                if isIPv6(ipText):
                    message['details']['destinationipv6address'] = ipText
                    message['details']['destinationipaddress'] = '0.0.0.0'
                    addError(message, 'plugin: {0} error: {1}'.format('ipFixUp.py', 'destinationipaddress is ipv6, moved'))
                elif not isIPv4(ipText):
                    if ipText == '-':
                        message['details']['destinationipaddress'] = '0.0.0.0'
                    else:
                        message['details']['destinationipaddress'] = '0.0.0.0'
                        addError(message, 'plugin: {0} error: {1}:{2}'.format('ipFixUp.py', 'destinationipaddress is invalid', ipText))

            if 'src' in message['details'].keys():
                ipText = message['details']['src']
                if isIPv4(ipText):
                    message['details']['sourceipaddress'] = ipText
                if isIPv6(ipText):
                    message['details']['sourceipv6address'] = ipText

            if 'srcip' in message['details'].keys():
                ipText = message['details']['srcip']
                if isIPv4(ipText):
                    message['details']['sourceipaddress'] = ipText
                if isIPv6(ipText):
                    message['details']['sourceipv6address'] = ipText
            if 'dst' in message['details'].keys():
                ipText = message['details']['dst']
                if isIPv4(ipText):
                    message['details']['destinationipaddress'] = ipText
                if isIPv6(ipText):
                    message['details']['destinationipv6address'] = ipText

            if 'dstip' in message['details'].keys():
                ipText = message['details']['dstip']
                if isIPv4(ipText):
                    message['details']['destinationipaddress'] = ipText
                if isIPv6(ipText):
                    message['details']['destinationipv6address'] = ipText

        return message

        