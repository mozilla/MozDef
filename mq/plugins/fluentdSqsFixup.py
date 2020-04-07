# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# Copyright (c) 2015 Mozilla Corporation
#
# This script copies the format/handling mechanism of ipFixup.py (git f5734b0c7e412424b44a6d7af149de6250fc70a2)

import netaddr
from mozdef_util.utilities.toUTC import toUTC


def isIPv4(ip):
    try:
        return netaddr.valid_ipv4(ip)
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
        self.registration = ['nubis_events_non_prod', 'nubis_events_prod']
        self.priority = 15

    def onMessage(self, message, metadata):
        """
        Ensure all messages have the mandatory mozdef fields
        """

        # Making sufficiently sure this is a fluentd-forwarded message from
        # fluentd SQS plugin, so that we don't spend too much time on other
        # message types
        if 'az' not in message and 'instance_id' not in message and '__tag' not in message:
            return (message, metadata)

        if 'details' not in message:
            message['details'] = dict()

        if 'summary' not in message and 'message' in message:
            message['summary'] = message['message']

        if 'utctimestamp' not in message and 'time' in message:
            message['utctimestamp'] = toUTC(message['time']).isoformat()

        # Bro format of {u'Timestamp': 1.482437837e+18}
        if 'utctimestamp' not in message and 'Timestamp' in message:
            message['utctimestamp'] = toUTC(message['Timestamp']).isoformat()

        # host is used to store dns-style-ip entries in AWS, for ex
        # ip-10-162-8-26 is 10.162.8.26. obviously there is no strong guarantee
        # that this is always trusted. It's better than nothing though. At the
        # time of writing, there is  no ipv6 support AWS-side for this kind of
        # field. It may be overridden later by a better field, if any exists
        if 'host' in message:
            tmp = message['host']
            if tmp.startswith('ip-'):
                ipText = tmp.split('ip-')[1].replace('-', '.')
                if isIPv4(ipText):
                    if 'destinationipaddress' not in message:
                        message['details']['destinationipaddress'] = ipText
                    if 'destinationipv4address' not in message:
                        message['details']['destinationipv4address'] = ipText
                else:
                    message['details']['destinationipaddress'] = '0.0.0.0'
                    message['details']['destinationipv4address'] = '0.0.0.0'
                    addError(message,
                             'plugin: {0} error: {1}:{2}'.format(
                                 'fluentSqsFixUp.py',
                                 'destinationipaddress is invalid',
                                 ipText))
            if 'hostname' not in message:
                message['hostname'] = tmp

        # All messages with __tag 'ec2.forward*' are actually syslog forwarded
        # messages, so classify as such
        if '__tag' in message:
            tmp = message['__tag']
            if tmp.startswith('ec2.forward'):
                message['category'] = 'syslog'
                message['source'] = 'syslog'

        if 'ident' in message:
            tmp = message['ident']
            message['details']['program'] = tmp
            if 'processname' not in message and 'program' in message['details']:
                message['processname'] = message['details']['program']
            if 'processid' not in message and 'pid' in message:
                message['processid'] = message['pid']
            else:
                message['processid'] = 0
            # Unknown really, but this field is mandatory.
            if 'severity' not in message:
                message['severity'] = 'INFO'

        # We already have the time of event stored in 'timestamp' so we don't
        # need 'time'
        if 'time' in message:
            message.pop('time')

        # Any remaining keys which aren't mandatory fields should be moved
        # to details
        # https://mozdef.readthedocs.io/en/latest/usage.html#mandatory-fields
        original_keys = list(message.keys())
        for key in original_keys:
            if key not in [
                    'summary',
                    'utctimestamp',
                    'hostname',
                    'category',
                    'source',
                    'processname',
                    'processid',
                    'severity',
                    'tags',
                    'details']:
                message['details'][key] = message[key]
                message.pop(key)

        return (message, metadata)
