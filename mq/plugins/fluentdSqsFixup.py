# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
# Copyright (c) 2015 Mozilla Corporation
#
# This script copies the format/handling mechanism of ipFixup.py (git f5734b0c7e412424b44a6d7af149de6250fc70a2)
#
# Contributors:
# Guillaume Destuynder kang@mozilla.com
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
           as a list of lower case strings or values to match with an event's dictionary of keys or values
           set the priority if you have a preference for order of plugins to run.
           0 goes first, 100 is assumed/default if not sent
        '''
        # ask for anything that could house an IP address
        self.registration = ['nubis_events_non_prod', 'nubis_events_prod']
        self.priority = 15

    def onMessage(self, message, metadata):
        '''
        Ensure all messages that have 'details' have the mandatory mozdef fields
        '''
        details = message['details']

        # shortcuts if we're not interested in the message
        if not 'details' in message.keys():
            return (message, metadata)

        # Making sufficiently sure this is a fluentd-forwarded message from fluentd SQS plugin, so that we don't spend
        # too much time on other message types
        if (not 'az' in details.keys()) and (not 'instance_id' in details.keys()
            and (not '__tag' in details.keys())):
            return (message, metadata)

        # host is used to store dns-style-ip entries in AWS, for ex ip-10-162-8-26 is 10.162.8.26.
        # obviously there is no strong garantee that this is always trusted. It's better than nothing though.
        # At the time of writting, there is no ipv6 support AWS-side for this kind of field.
        # It may be overriden later by a better field, if any exists.
        if 'host' in details.keys():
            tmp = details['host']
            if tmp.startswith('ip-'):
                ipText = tmp.split('ip-')[1].replace('-', '.')
                if isIPv4(ipText):
                    if 'destinationipaddress' not in details.keys():
                        details['destinationipaddress'] = ipText
                    if 'destinationipv4address' not in details.keys():
                        details['destinationipv4address'] = ipText
                else:
                    details['destinationipaddress'] = '0.0.0.0'
                    details['destinationipv4address'] = '0.0.0.0'
                    addError(message, 'plugin: {0} error: {1}:{2}'.format('fluentSqsFixUp.py', 'destinationipaddress is invalid', ipText))
            if not 'hostname' in message.keys(): message['hostname'] = tmp

        # All messages with __tag 'ec2.forward*' are actually syslog forwarded messages, so classify as such
        if '__tag' in details.keys():
            tmp = details['__tag']
            if tmp.startswith('ec2.forward'):
                message['category'] = 'syslog'
                message['source'] = 'syslog'

        if 'ident' in details.keys():
            tmp = details['ident']
            details['program'] = tmp
            if (not 'processname' in message.keys()) and ('program' in details.keys()):
                message['processname'] = details['program']
            if (not 'processid' in message.keys()) and ('pid' in details.keys()):
                message['processid'] = details['pid']
            else:
                message['processid'] = 0
            # Unknown really, but this field is mandatory.
            if not 'severity' in message.keys(): message['severity'] = 'INFO'

        # We already have the time of event stored in 'timestamp' so we don't need 'time'
        if 'time' in details.keys():
          details.pop('time')

        return (message, metadata)
