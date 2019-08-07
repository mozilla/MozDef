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
        self.registration = ['observium']
        self.priority = 5
        self.regex = re.compile(r'(?P<alert_type>\S+): \[(?P<source_host>\S+)\] \[(?P<entity_type>\S+)\] \[(?P<entity>.*)\] (?P<alert_message>.*)')

    def onMessage(self, message, metadata):
        if 'details' in message:
            if 'program' in message['details']:
                if 'Observium' == message['details']['program']:
                    msg_unparsed = message['summary']
                    search = re.search(self.regex, msg_unparsed)
                    if search:
                        message['hostname'] = search.group('source_host')
                        message['details']['alert_type'] = search.group('alert_type')
                        message['details']['entity_type'] = search.group('entity_type')
                        message['details']['entity'] = search.group('entity')
                        message['details']['alert_message'] = search.group('alert_message')
                        # tag the message
                        if 'tags' in message and isinstance(message['tags'], list):
                            message['tags'].append('alert')
                        else:
                            message['tags'] = ['alert']

        return (message, metadata)
