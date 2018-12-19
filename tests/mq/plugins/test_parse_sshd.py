# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
# Copyright (c) 2017 Mozilla Corporation

import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), "../../../mq/plugins"))
from parse_sshd import message
import copy

accept_message = {}
accept_message['_type'] = 'event'
accept_message = {}
accept_message['utctimestamp'] = '2017-08-24T22:49:42+00:00'
accept_message['timestamp'] = '2017-08-24T22:49:42+00:00'
accept_message['receivedtimestamp'] = '2017-08-24T22:49:42+00:00'
accept_message['category'] = 'syslog'
accept_message['processid'] = '0'
accept_message['processname'] = 'sshd'
accept_message['severity'] = '7'
accept_message['hostname'] = 'syslog1.private.scl3.mozilla.com'
accept_message['mozdefhostname'] = 'mozdef4.private.scl3.mozilla.com'
accept_message['eventsource'] = 'systemlogs'
accept_message['details'] = {}
accept_message['details']['processid'] = '5413'
accept_message['details']['sourceipv4address'] = '10.22.74.208'
accept_message['details']['hostname'] = 'mysuperhost.somewhere.com'
accept_message['details']['program'] = 'sshd'
accept_message['details']['sourceipaddress'] = '10.22.74.208'


# Short username, RSA fpr present
class TestSSHDAcceptedMessageV1():
    def setup(self):

        self.msgobj = message()
        self.msg = copy.deepcopy(accept_message)
        self.msg['summary'] = 'Accepted publickey for user1 from 10.22.74.208 port 26388 ssh2: RSA 1f:c9:4c:90:bc:fb:72:c7:4d:02:da:07:ed:fe:07:ac'

    def test_onMessage(self):
        metadata = {}
        metadata['doc_type'] = 'event'

        (retmessage, retmeta) = self.msgobj.onMessage(self.msg, metadata)

        assert retmessage is not None
        assert retmeta is not None
        assert retmessage['details']['username'] == 'user1'
        assert retmessage['details']['rsakeyfingerprint'] == '1f:c9:4c:90:bc:fb:72:c7:4d:02:da:07:ed:fe:07:ac'
        assert retmessage['details']['authmethod'] == 'publickey'
        assert retmessage['details']['sourceport'] == '26388'
        assert retmessage['details']['authstatus'] == 'Accepted'
        assert retmessage['details']['sourceipaddress'] == '10.22.74.208'

# Long Username and SHA256 fpr present


class TestSSHDAcceptedMessageV2():
    def setup(self):

        self.msgobj = message()
        self.msg = copy.deepcopy(accept_message)
        self.msg['summary'] = 'Accepted publickey for user1@domainname.com from 10.22.248.134 port 52216 ssh2: RSA SHA256:1fPhSawXQzFDrJoN2uSos2nGg3wS3oGp15x8/HR+pBc'

    def test_onMessage(self):
        metadata = {}
        metadata['doc_type'] = 'event'

        (retmessage, retmeta) = self.msgobj.onMessage(self.msg, metadata)

        assert retmessage is not None
        assert retmeta is not None
        assert retmessage['details']['username'] == 'user1@domainname.com'
        assert retmessage['details']['rsakeyfingerprint'] == 'SHA256:1fPhSawXQzFDrJoN2uSos2nGg3wS3oGp15x8/HR+pBc'
        assert retmessage['details']['authmethod'] == 'publickey'
        assert retmessage['details']['sourceport'] == '52216'
        assert retmessage['details']['authstatus'] == 'Accepted'
        assert retmessage['details']['sourceipaddress'] == '10.22.248.134'


# Long username
class TestSSHDAcceptedMessageV3():
    def setup(self):

        self.msgobj = message()
        self.msg = copy.deepcopy(accept_message)
        self.msg['summary'] = 'Accepted publickey for user1@domainname.com from 10.22.74.208 port 26388 ssh2: RSA 1f:c9:4c:90:bc:fb:72:c7:4d:02:da:07:ed:fe:07:ac'

    def test_onMessage(self):
        metadata = {}
        metadata['doc_type'] = 'event'

        (retmessage, retmeta) = self.msgobj.onMessage(self.msg, metadata)

        assert retmessage is not None
        assert retmeta is not None
        assert retmessage['details']['username'] == 'user1@domainname.com'
        assert retmessage['details']['rsakeyfingerprint'] == '1f:c9:4c:90:bc:fb:72:c7:4d:02:da:07:ed:fe:07:ac'
        assert retmessage['details']['authmethod'] == 'publickey'
        assert retmessage['details']['sourceport'] == '26388'
        assert retmessage['details']['authstatus'] == 'Accepted'
        assert retmessage['details']['sourceipaddress'] == '10.22.74.208'


# Short username, RSA fpr missing
class TestSSHDAcceptedMessageV4():
    def setup(self):

        self.msgobj = message()
        self.msg = copy.deepcopy(accept_message)
        self.msg['summary'] = 'Accepted publickey for user1 from 10.22.74.208 port 26388 ssh2'

    def test_onMessage(self):
        metadata = {}
        metadata['doc_type'] = 'event'

        (retmessage, retmeta) = self.msgobj.onMessage(self.msg, metadata)

        assert retmessage is not None
        assert retmeta is not None
        assert retmessage['details']['username'] == 'user1'
        assert retmessage['details']['rsakeyfingerprint'] is None
        assert retmessage['details']['authmethod'] == 'publickey'
        assert retmessage['details']['sourceport'] == '26388'
        assert retmessage['details']['authstatus'] == 'Accepted'
        assert retmessage['details']['sourceipaddress'] == '10.22.74.208'


# PAM session opened for user
class TestSSHDPAMSessionOpenedMessageV1():
    def setup(self):

        self.msgobj = message()
        self.msg = copy.deepcopy(accept_message)
        self.msg['summary'] = 'pam_unix(sshd:session): session opened for user user1 by (uid=0)'

    def test_onMessage(self):
        metadata = {}
        metadata['doc_type'] = 'event'

        (retmessage, retmeta) = self.msgobj.onMessage(self.msg, metadata)

        assert retmessage is not None
        assert retmeta is not None
        assert retmessage['details']['username'] == 'user1'


# PAM session closed for user
class TestSSHDPAMSessionClosedMessageV1():
    def setup(self):

        self.msgobj = message()
        self.msg = copy.deepcopy(accept_message)
        self.msg['summary'] = 'pam_unix(sshd:session): session closed for user user1'

    def test_onMessage(self):
        metadata = {}
        metadata['doc_type'] = 'event'

        (retmessage, retmeta) = self.msgobj.onMessage(self.msg, metadata)

        assert retmessage is not None
        assert retmeta is not None
        assert retmessage['details']['username'] == 'user1'


# Postponed preauth - short, simple username
class TestSSHDPostponedMessageV1():
    def setup(self):

        self.msgobj = message()
        self.msg = copy.deepcopy(accept_message)
        self.msg['summary'] = 'Postponed publickey for user1 from 10.22.75.209 port 37486 ssh2'

    def test_onMessage(self):
        metadata = {}
        metadata['doc_type'] = 'event'

        (retmessage, retmeta) = self.msgobj.onMessage(self.msg, metadata)

        assert retmessage is not None
        assert retmeta is not None
        assert retmessage['details']['username'] == 'user1'
        assert retmessage['details']['authmethod'] == 'publickey'


# Postponed preauth - long, simple username
class TestSSHDPostponedMessageV2():
    def setup(self):

        self.msgobj = message()
        self.msg = copy.deepcopy(accept_message)
        self.msg['summary'] = 'Postponed publickey for user1 from 10.22.75.209 port 37486 ssh2 [preauth]'

    def test_onMessage(self):
        metadata = {}
        metadata['doc_type'] = 'event'

        (retmessage, retmeta) = self.msgobj.onMessage(self.msg, metadata)

        assert retmessage is not None
        assert retmeta is not None
        assert retmessage['details']['username'] == 'user1'
        assert retmessage['details']['authmethod'] == 'publickey'


# Postponed preauth - long username
class TestSSHDPostponedMessageV3():
    def setup(self):

        self.msgobj = message()
        self.msg = copy.deepcopy(accept_message)
        self.msg['summary'] = 'Postponed publickey for user1@somewhere.com from 10.22.75.209 port 37486 ssh2 [preauth]'

    def test_onMessage(self):
        metadata = {}
        metadata['doc_type'] = 'event'

        (retmessage, retmeta) = self.msgobj.onMessage(self.msg, metadata)

        assert retmessage is not None
        assert retmeta is not None
        assert retmessage['details']['username'] == 'user1@somewhere.com'
        assert retmessage['details']['authmethod'] == 'publickey'


# Starting session
class TestSSHDStartingSessionV1():
    def setup(self):

        self.msgobj = message()
        self.msg = copy.deepcopy(accept_message)
        self.msg['summary'] = 'Starting session: command for user1 from 10.22.128.93 port 51748'

    def test_onMessage(self):
        metadata = {}
        metadata['doc_type'] = 'event'

        (retmessage, retmeta) = self.msgobj.onMessage(self.msg, metadata)

        assert retmessage is not None
        assert retmeta is not None
        assert retmessage['details']['username'] == 'user1'
        assert retmessage['details']['sessiontype'] == 'command'
        assert retmessage['details']['sourceipaddress'] == '10.22.128.93'
        assert retmessage['details']['sourceport'] == '51748'


# Starting session
class TestSSHDStartingSessionV2():
    def setup(self):

        self.msgobj = message()
        self.msg = copy.deepcopy(accept_message)
        self.msg['summary'] = 'Starting session: shell on pts/0 for user2 from 10.22.252.6 port 59983'

    def test_onMessage(self):
        metadata = {}
        metadata['doc_type'] = 'event'

        (retmessage, retmeta) = self.msgobj.onMessage(self.msg, metadata)

        assert retmessage is not None
        assert retmeta is not None
        assert retmessage['details']['username'] == 'user2'
        assert retmessage['details']['sessiontype'] == 'shell'
        assert retmessage['details']['sourceipaddress'] == '10.22.252.6'
        assert retmessage['details']['sourceport'] == '59983'
        assert retmessage['details']['device'] == 'pts/0'
