# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# Copyright (c) 2017 Mozilla Corporation

import copy

from mq.plugins.parse_su import message

session_su = {}
session_su['utctimestamp'] = '2017-08-24T22:49:42+00:00'
session_su['timestamp'] = '2017-08-24T22:49:42+00:00'
session_su['receivedtimestamp'] = '2017-08-24T22:49:42+00:00'
session_su['category'] = 'syslog'
session_su['processid'] = '0'
session_su['severity'] = '7'
session_su['eventsource'] = 'systemlogs'
session_su['hostname'] = 'syslog1.private.scl3.mozilla.com'
session_su['mozdefhostname'] = 'mozdef4.private.scl3.mozilla.com'
session_su['details'] = {}
session_su['details']['program'] = 'su'
session_su['details']['hostname'] = 'irc1.dmz.scl3.mozilla.com'


class TestSuSessionOpenedMessageV1():
    def setup(self):

        self.msgobj = message()
        self.msg = copy.deepcopy(session_su)
        self.msg['summary'] = 'pam_unix(su:session): session opened for user user1 by (uid=0)'

    def test_onMessage(self):
        metadata = {}

        (retmessage, retmeta) = self.msgobj.onMessage(self.msg, metadata)

        assert retmessage is not None
        assert retmeta is not None
        assert retmessage['details']['originuser'] is None
        assert retmessage['details']['status'] == 'opened'
        assert retmessage['details']['uid'] == '0'
        assert retmessage['details']['username'] == 'user1'


#
class TestSuSessionOpenedMessageV2():
    def setup(self):

        self.msgobj = message()
        self.msg = copy.deepcopy(session_su)
        self.msg['summary'] = 'pam_unix(su:session): session opened for user user2 by user3(uid=0)'

    def test_onMessage(self):
        metadata = {}

        (retmessage, retmeta) = self.msgobj.onMessage(self.msg, metadata)

        assert retmessage is not None
        assert retmeta is not None
        assert retmessage['details']['originuser'] == 'user3'
        assert retmessage['details']['status'] == 'opened'
        assert retmessage['details']['uid'] == '0'
        assert retmessage['details']['username'] == 'user2'


#
class TestSuSessionOpenedMessageV3():
    def setup(self):

        self.msgobj = message()
        self.msg = copy.deepcopy(session_su)
        self.msg['summary'] = 'pam_unix(su-l:session): session opened for user user4 by (uid=0)'

    def test_onMessage(self):
        metadata = {}

        (retmessage, retmeta) = self.msgobj.onMessage(self.msg, metadata)

        assert retmessage is not None
        assert retmeta is not None
        assert retmessage['details']['originuser'] is None
        assert retmessage['details']['status'] == 'opened'
        assert retmessage['details']['uid'] == '0'
        assert retmessage['details']['username'] == 'user4'


#
class TestSuSessionOpenedMessageV4():
    def setup(self):

        self.msgobj = message()
        self.msg = copy.deepcopy(session_su)
        self.msg['summary'] = 'pam_unix(su-l:session): session opened for user user5 by user6(uid=0)'

    def test_onMessage(self):
        metadata = {}

        (retmessage, retmeta) = self.msgobj.onMessage(self.msg, metadata)

        assert retmessage is not None
        assert retmeta is not None
        assert retmessage['details']['originuser'] == 'user6'
        assert retmessage['details']['status'] == 'opened'
        assert retmessage['details']['uid'] == '0'
        assert retmessage['details']['username'] == 'user5'


#
class TestSuSessionClosedMessageV1():
    def setup(self):

        self.msgobj = message()
        self.msg = copy.deepcopy(session_su)
        self.msg['summary'] = 'pam_unix(su:session): session closed for user user7'

    def test_onMessage(self):
        metadata = {}

        (retmessage, retmeta) = self.msgobj.onMessage(self.msg, metadata)

        assert retmessage is not None
        assert retmeta is not None
        assert retmessage['details']['originuser'] is None
        assert retmessage['details']['status'] == 'closed'
        assert retmessage['details']['uid'] is None
        assert retmessage['details']['username'] == 'user7'
