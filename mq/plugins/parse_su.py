# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# Copyright (c) 2017 Mozilla Corporation

import re


class message(object):

    def __init__(self):
        '''
        takes an incoming su message
        and parses it to extract data points
        '''

        self.registration = ['sshd']
        self.priority = 5

    def onMessage(self, message, metadata):

        self.session_regexp = re.compile(r'^pam_unix\(su(?:-l)?\:session\)\: session (?P<status>\w+) for user (?P<username>\w+)(?: (?:by (?:(?P<originuser>\w+))?\(uid\=(?P<uid>[0-9]+)\)?)?)?$')

        if 'details' in message:
            if 'program' in message['details']:
                if message['details']['program'] == 'su':
                    msg_unparsed = message['summary']
                    if msg_unparsed.startswith('pam_unix'):
                        session_search = re.search(self.session_regexp, msg_unparsed)
                        if session_search:
                            message['details']['originuser'] = session_search.group('originuser')
                            message['details']['status'] = session_search.group('status')
                            message['details']['uid'] = session_search.group('uid')
                            message['details']['username'] = session_search.group('username')

        return (message, metadata)
