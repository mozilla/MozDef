# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
# Copyright (c) 2017 Mozilla Corporation

import sys
import os
import re
sys.path.append(os.path.join(os.path.dirname(__file__), "../../lib"))
from utilities.toUTC import toUTC


class message(object):

    def __init__(self):
        self.registration = ['sshd']
        self.priority = 5


    def onMessage(self, message, metadata):

        self.accepted_regex = re.compile('^(?P<authstatus>\w+) (?P<authmethod>\w+) for (?P<username>[a-zA-Z0-9\@._-]+) from (?P<sourceipaddress>\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}) port (?P<sourceport>\d{1,5}) ssh2(\:\sRSA\s)?(?:(?P<rsakeyfingerprint>(\S+)))?$')
        self.session_opened_regex = re.compile('^pam_unix\(sshd\:session\)\: session (opened|closed) for user (?P<username>[a-zA-Z0-9\@._-]+)(?: by \(uid\=\d*\))?$')
        self.postponed_regex = re.compile('^Postponed (?P<authmethod>\w+) for (?P<username>[a-zA-Z0-9\@._-]+) from (?P<sourceipaddress>\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}) port (?P<sourceport>\d{1,5}) ssh2(?: \[preauth\])?$')
        self.starting_session_regex = re.compile('^Starting session: (?P<sessiontype>\w+)(?: on )?(?P<device>pts/0)? for (?P<username>[a-zA-Z0-9\@._-]+) from (?P<sourceipaddress>\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}) port (?P<sourceport>\d{1,5})$')

        if 'processname' in message or 'details' in message:
            if ('program' in message['details'] and message['details']['program'] == 'sshd') or ('processname' in message and message['processname'] == 'sshd'):
                    msg_unparsed = message['summary']
                    if msg_unparsed.startswith('Accepted'):
                        accepted_search = re.search(self.accepted_regex, msg_unparsed)
                        if accepted_search:
                            message['details']['authstatus'] = accepted_search.group('authstatus')
                            message['details']['authmethod'] = accepted_search.group('authmethod')
                            message['details']['username'] = accepted_search.group('username')
                            message['details']['sourceipaddress'] = accepted_search.group('sourceipaddress')
                            message['details']['sourceport'] = accepted_search.group('sourceport')
                            message['details']['rsakeyfingerprint'] = accepted_search.group('rsakeyfingerprint')
                    if msg_unparsed.startswith('pam_unix'):
                        session_opened_search = re.search(self.session_opened_regex, msg_unparsed)
                        if session_opened_search:
                            message['details']['username'] = session_opened_search.group('username')
                    if msg_unparsed.startswith('Postponed'):
                        postponed_search = re.search(self.postponed_regex, msg_unparsed)
                        if postponed_search:
                            message['details']['username'] = postponed_search.group('username')
                            message['details']['authmethod'] = postponed_search.group('authmethod')
                    if msg_unparsed.startswith('Starting session'):
                        starting_session_search = re.search(self.starting_session_regex, msg_unparsed)
                        if starting_session_search:
                            message['details']['sessiontype'] = starting_session_search.group('sessiontype')
                            message['details']['username'] = starting_session_search.group('username')
                            message['details']['sourceipaddress'] = starting_session_search.group('sourceipaddress')
                            message['details']['sourceport'] = starting_session_search.group('sourceport')
                            message['details']['device'] = starting_session_search.group('device')

        return (message, metadata)
