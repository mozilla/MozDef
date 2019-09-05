# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# Copyright (c) 2014 Mozilla Corporation

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
    if 'errors' not in message:
        message['errors'] = list()
    if isinstance(message['errors'], list):
        message['errors'].append(error)


class message(object):
    def __init__(self):
        '''register our criteria for being passed a message
           as a list of lower case strings or values to match with an event's dictionary of keys or values
           set the priority if you have a preference for order of plugins to run.
           0 goes first, 100 is assumed/default if not sent
        '''
        # ask for anything that could house an IP address
        self.registration = ['sourceipaddress', 'destinationipaddress', 'src', 'dst', 'srcip', 'dstip', 'http_x_forwarded_for']
        self.priority = 15

    def onMessage(self, message, metadata):
        '''
        Examine possible ip addresses for the following:
          ipv6 in an ipv4 field
          ipv4 in another field
          '-' or other invalid ip in the ip field
        Also sets ipv4 in two fields:
            ipaddress (decimal mapping IP)
            ipv4address (string mapping)
            While the IP field-type serves for IPv4 or IPv6,
            it is not quite mature yet as kibana lacks filtering
            to differentiate between IPv4 and IPv6, so always
            having a string version is the most flexible option.
        '''

        if 'details' in message:
            # forwarded header can be spoofed, so try it first,
            # but override later if we've a better field.
            if 'http_x_forwarded_for' in message['details']:
                # should be a comma delimited list of ips with the original client listed first
                ipText = message['details']['http_x_forwarded_for'].split(',')[0]
                if isIPv4(ipText) and 'sourceipaddress' not in message['details']:
                    message['details']['sourceipaddress'] = ipText
                if isIPv4(ipText) and 'sourceipv4address' not in message['details']:
                    message['details']['sourceipv4address'] = ipText
                if isIPv6(ipText) and 'sourceipv6address' not in message['details']:
                    message['details']['sourceipv6address'] = ipText

            if 'sourceipaddress' in message['details']:
                ipText = message['details']['sourceipaddress']
                if isIPv6(ipText):
                    message['details']['sourceipv6address'] = ipText
                    message['details']['sourceipaddress'] = '0.0.0.0'
                    addError(message, 'plugin: {0} error: {1}'.format('ipFixUp.py', 'sourceipaddress is ipv6, moved'))
                elif isIPv4(ipText):
                    message['details']['sourceipv4address'] = ipText
                else:
                    # Smells like a hostname, let's save it as source field
                    message['details']['source'] = message['details']['sourceipaddress']
                    message['details']['sourceipaddress'] = None

            if 'destinationipaddress' in message['details']:
                ipText = message['details']['destinationipaddress']
                if isIPv6(ipText):
                    message['details']['destinationipv6address'] = ipText
                    message['details']['destinationipaddress'] = '0.0.0.0'
                    addError(message, 'plugin: {0} error: {1}'.format('ipFixUp.py', 'destinationipaddress is ipv6, moved'))
                elif isIPv4(ipText):
                    message['details']['destinationipv4address'] = ipText
                else:
                    # Smells like a hostname, let's save it as destination field
                    message['details']['destination'] = message['details']['destinationipaddress']
                    message['details']['destinationipaddress'] = None

            if 'src' in message['details']:
                ipText = message['details']['src']
                if isIPv4(ipText):
                    message['details']['sourceipaddress'] = ipText
                    message['details']['sourceipv4address'] = ipText
                if isIPv6(ipText):
                    message['details']['sourceipv6address'] = ipText

            if 'srcip' in message['details']:
                ipText = message['details']['srcip']
                if isIPv4(ipText):
                    message['details']['sourceipaddress'] = ipText
                    message['details']['sourceipv4address'] = ipText
                if isIPv6(ipText):
                    message['details']['sourceipv6address'] = ipText
            if 'dst' in message['details']:
                ipText = message['details']['dst']
                if isIPv4(ipText):
                    message['details']['destinationipaddress'] = ipText
                    message['details']['destinationipv4address'] = ipText
                if isIPv6(ipText):
                    message['details']['destinationipv6address'] = ipText

            if 'dstip' in message['details']:
                ipText = message['details']['dstip']
                if isIPv4(ipText):
                    message['details']['destinationipaddress'] = ipText
                    message['details']['destinationipv4address'] = ipText
                if isIPv6(ipText):
                    message['details']['destinationipv6address'] = ipText

            if 'cluster_client_ip' in message['details']:
                ipText = message['details']['cluster_client_ip']
                if isIPv4(ipText):
                    message['details']['sourceipaddress'] = ipText
                if isIPv6(ipText):
                    message['details']['sourceipv6address'] = ipText

        return (message, metadata)
