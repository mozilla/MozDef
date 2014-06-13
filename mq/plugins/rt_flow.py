# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
# Copyright (c) 2014 Mozilla Corporation
#
# Contributors:
# Anthony Verez averez@mozilla.com

import re

class message(object):
    def __init__(self):
        '''register our criteria for being passed a message
           as a list of lower case strings or values to match with an event's dictionary of keys or values
           set the priority if you have a preference for order of plugins to run.
           0 goes first, 100 is assumed/default if not sent
        '''
        self.registration = ['RT_FLOW']
        self.priority = 5
        self.deny_regex = re.compile(r'%-RT_FLOW_SESSION_DENY: session denied (?P<src>([0-9]+\.[0-9]+\.[0-9]+\.[0-9]+))/(?P<srcport>[0-9]+)->(?P<dst>([0-9]+\.[0-9]+\.[0-9]+\.[0-9]+))/(?P<dstport>[0-9]+) (?P<service>\S+) (?P<proto>[0-9]+)\((?P<prototype>[0-9]+)\) (?P<policy>\S+) (?P<srczone>\S+) (?P<dstzone>\S+) UNKNOWN UNKNOWN N/A\(N/A\) (?P<interface>\S+)(\n)?')

    def onMessage(self, message, metadata):
        if 'details' in message.keys():
            if 'program' in message['details'].keys():
            	if 'RT_FLOW' == message['details']['program']:
            		msg_unparsed = message['summary']
            		if len(msg_unparsed) > 23 and msg_unparsed[:23] == '%-RT_FLOW_SESSION_DENY:':
            			deny_search = re.search(self.deny_regex, msg_unparsed)
            			if deny_search:
            				message['details']['src'] = deny_search.group('src')
            				message['details']['srcport'] = deny_search.group('srcport')
            				message['details']['dst'] = deny_search.group('dst')
            				message['details']['dstport'] = deny_search.group('dstport')
            				message['details']['service'] = deny_search.group('service')
            				message['details']['proto'] = deny_search.group('proto')
            				message['details']['prototype'] = deny_search.group('prototype')
            				message['details']['policy'] = deny_search.group('policy')
            				message['details']['srczone'] = deny_search.group('srczone')
            				message['details']['dstzone'] = deny_search.group('dstzone')
            				message['details']['interface'] = deny_search.group('interface')

        return (message, metadata)
