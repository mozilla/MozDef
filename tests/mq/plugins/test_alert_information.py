# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# Copyright (c) 2017 Mozilla Corporation

from mq.plugins.alert_information import message


class TestAlertInformationPlugin():
    def setup(self):
        self.plugin = message()

    def test_nonexistent_details(self):
        msg = {
            'category': 'someother',
        }
        (retmessage, retmeta) = self.plugin.onMessage(msg, {})
        assert retmessage == msg
        assert retmeta == {}

    def test_details_nondict(self):
        msg = {
            'category': 'someother',
            'details': 'alert_information value'
        }
        (retmessage, retmeta) = self.plugin.onMessage(msg, {})
        assert retmessage == msg
        assert retmeta == {}

    def test_nonexistent_alert_information(self):
        msg = {
            'details': {
                'somekey': 'somevalue'
            }
        }
        (retmessage, retmeta) = self.plugin.onMessage(msg, {})
        assert retmessage == msg
        assert retmeta == {}

    def test__alert_information_nondict(self):
        msg = {
            'details': {
                'alert_information': {
                    'somekey': 'some summary value'
                }
            }
        }
        (retmessage, retmeta) = self.plugin.onMessage(msg, {})
        assert retmessage == msg
        assert retmeta == {}

    def test_nonexistent_summary(self):
        msg = {
            'details': {
                'alert_information': {
                    'somekey': 'somevalue'
                }
            }
        }

        (retmessage, retmeta) = self.plugin.onMessage(msg, {})
        assert retmessage == msg
        assert retmeta == {}

    def test_good_event(self):
        msg = {
            'summary': 'some random summary',
            'details': {
                'alert_information': {
                    'summary': 'This is a good alert summary'
                }
            }
        }
        (retmessage, retmeta) = self.plugin.onMessage(msg, {})
        expected_message = {
            'details': {
                'alert_information': {
                    'summary': 'This is a good alert summary'
                }
            },
            'summary': 'This is a good alert summary'
        }
        assert retmessage == expected_message
        assert retmeta == {}
