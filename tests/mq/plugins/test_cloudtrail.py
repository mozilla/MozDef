# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# Copyright (c) 2017 Mozilla Corporation

from mq.plugins.cloudtrail import message


class TestCloudtrailPluginBadEvents():
    def setup(self):
        self.plugin = message()

    def test_nonexistent_source(self):
        msg = {
            "category": "someother",
        }
        (retmessage, retmeta) = self.plugin.onMessage(msg, {})
        assert retmessage == msg
        assert retmeta == {}

    def test_bad_source(self):
        msg = {
            "source": "someother",
            "hostname": "some.aws.amazon.com",
            "details": {}
        }
        (retmessage, retmeta) = self.plugin.onMessage(msg, {})
        assert retmessage == msg
        assert retmeta == {}

    def test_nonexistent_hostname(self):
        msg = {
            "source": "cloudtrail",
            "details": {}
        }
        (retmessage, retmeta) = self.plugin.onMessage(msg, {})
        assert retmessage == msg
        assert retmeta == {}

    def test_nonexistent_details(self):
        msg = {
            "source": "cloudtrail",
            "hostname": "some.aws.amazon.com"
        }
        (retmessage, retmeta) = self.plugin.onMessage(msg, {})
        assert retmessage == msg
        assert retmeta == {}


class TestCloudtrailPlugin():
    def setup(self):
        self.plugin = message()
        self.good_event = {
            "source": "cloudtrail",
            "hostname": "some.aws.amazon.com",
            "details": {
                "apiversion": "2015-12-01",
                "requestparameters": {
                    "somekey": "somevalue"
                }
            }
        }

    def test_apiversion_moved(self):
        (retmessage, retmeta) = self.plugin.onMessage(self.good_event, {})
        assert 'apiversion' not in retmessage['details']
        assert 'apiversion' in retmessage['details']['some.aws.amazon.com']
        assert retmessage['details']['some.aws.amazon.com']['apiversion'] == "2015-12-01"

    def test_requestparameters_moved(self):
        (retmessage, retmeta) = self.plugin.onMessage(self.good_event, {})
        assert 'requestparameters' not in retmessage['details']
        assert 'requestparameters' in retmessage['details']['some.aws.amazon.com']
        assert retmessage['details']['some.aws.amazon.com']['requestparameters'] == {"somekey": "somevalue"}
