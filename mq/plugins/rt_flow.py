# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# Copyright (c) 2014 Mozilla Corporation

import re


class message(object):
    def __init__(self):
        '''register our criteria for being passed a message
           as a list of lower case strings or values to match with an event's dictionary of keys or values
           set the priority if you have a preference for order of plugins to run.
           0 goes first, 100 is assumed/default if not sent
        '''
        self.registration = ['rt_flow']
        self.priority = 5
        self.deny_regex = re.compile(r'%-RT_FLOW_SESSION_DENY: session denied (?P<src>([0-9]+\.[0-9]+\.[0-9]+\.[0-9]+))/(?P<srcport>[0-9]+)->(?P<dst>([0-9]+\.[0-9]+\.[0-9]+\.[0-9]+))/(?P<dstport>[0-9]+) (?P<service>\S+) (?P<proto>[0-9]+)\((?P<prototype>[0-9]+)\) (?P<policy>\S+) (?P<srczone>\S+) (?P<dstzone>\S+) UNKNOWN UNKNOWN N/A\(N/A\) (?P<interface>\S+)(\n)?')
        self.create_regex = re.compile(r'%-RT_FLOW_SESSION_CREATE: session created (?P<src>([0-9]+\.[0-9]+\.[0-9]+\.[0-9]+))/(?P<srcport>[0-9]+)->(?P<dst>([0-9]+\.[0-9]+\.[0-9]+\.[0-9]+))/(?P<dstport>[0-9]+) (?P<service>\S+) (?P<src2>([0-9]+\.[0-9]+\.[0-9]+\.[0-9]+))/(?P<srcport2>[0-9]+)->(?P<dst2>([0-9]+\.[0-9]+\.[0-9]+\.[0-9]+))/(?P<dstport2>[0-9]+) (?P<srcnatrule>\S+) (?P<dstnatrule>\S+) (?P<protocol>\S+) (?P<policy>\S+) (?P<srczone>\S+) (?P<dstzone>\S+) (?P<sessionid>\S+) N/A\(N/A\) (?P<interface>\S+)(\n)?')

    def onMessage(self, message, metadata):
        if 'details' in message:
            if 'program' in message['details']:
                if 'RT_FLOW' == message['details']['program']:
                    msg_unparsed = message['summary']
                    if msg_unparsed.startswith('%-RT_FLOW_SESSION_DENY:'):
                        deny_search = re.search(self.deny_regex, msg_unparsed)
                        if deny_search:
                            message['details']['action'] = 'denied'
                            message['details']['sourceipaddress'] = deny_search.group('src')
                            message['details']['sourceport'] = deny_search.group('srcport')
                            message['details']['destinationipaddress'] = deny_search.group('dst')
                            message['details']['destinationport'] = deny_search.group('dstport')
                            message['details']['service'] = deny_search.group('service')
                            message['details']['protocol'] = deny_search.group('proto')
                            message['details']['protocoltype'] = deny_search.group('prototype')
                            message['details']['policy'] = deny_search.group('policy')
                            message['details']['sourcezone'] = deny_search.group('srczone')
                            message['details']['destinationzone'] = deny_search.group('dstzone')
                            message['details']['interface'] = deny_search.group('interface')
                    if msg_unparsed.startswith('%-RT_FLOW_SESSION_CREATE:'):
                        create_search = re.search(self.create_regex, msg_unparsed)
                        if create_search:
                            message['details']['action'] = 'created'
                            message['details']['sourceipaddress'] = create_search.group('src')
                            message['details']['sourceport'] = create_search.group('srcport')
                            message['details']['destinationipaddress'] = create_search.group('dst')
                            message['details']['destinationport'] = create_search.group('dstport')
                            message['details']['service'] = create_search.group('service')
                            message['details']['sourcenatrule'] = create_search.group('srcnatrule')
                            message['details']['destinationnatrule'] = create_search.group('dstnatrule')
                            message['details']['protocol'] = create_search.group('protocol')
                            message['details']['policy'] = create_search.group('policy')
                            message['details']['sourcezone'] = create_search.group('srczone')
                            message['details']['destinationzone'] = create_search.group('dstzone')
                            message['details']['sessionid'] = create_search.group('sessionid')
                            message['details']['interface'] = create_search.group('interface')

        return (message, metadata)
