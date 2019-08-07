# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# Copyright (c) 2017 Mozilla Corporation

from mq.plugins.large_strings import message


class TestLargeStrings():
    def setup(self):
        self.plugin = message()

    def test_large_details_message(self):
        msg = {
            'category': 'someother',
            'details': {
                'message': 'a' * 8000
            }
        }
        expected_details_message = 'a' * 3000
        expected_details_message += ' ...'
        expected_msg = {
            'category': 'someother',
            'details': {
                'message': expected_details_message
            }
        }
        (retmessage, retmeta) = self.plugin.onMessage(msg, {})
        assert retmessage == expected_msg
        assert retmeta == {}

    def test_large_details_cmdline(self):
        msg = {
            'category': 'someother',
            'details': {
                'cmdline': 'a' * 8000
            }
        }
        expected_details_cmdline = 'a' * 3000
        expected_details_cmdline += ' ...'
        expected_msg = {
            'category': 'someother',
            'details': {
                'cmdline': expected_details_cmdline
            }
        }
        (retmessage, retmeta) = self.plugin.onMessage(msg, {})
        assert retmessage == expected_msg
        assert retmeta == {}

    def test_large_summary(self):
        msg = {
            'category': 'someother',
            'summary': 'a' * 8000
        }
        expected_summary = 'a' * 3000
        expected_summary += ' ...'
        expected_msg = {
            'category': 'someother',
            'summary': expected_summary
        }
        (retmessage, retmeta) = self.plugin.onMessage(msg, {})
        assert retmessage == expected_msg
        assert retmeta == {}

    def normal_sized_message_without_key(self):
        msg = {
            'category': 'someother',
        }
        (retmessage, retmeta) = self.plugin.onMessage(msg, {})
        assert retmessage == msg
        assert retmeta == {}

    def normal_sized_message_with_good_key(self):
        msg = {
            'category': 'someother',
            'details': {
                'message': 'A random message string'
            }
        }
        (retmessage, retmeta) = self.plugin.onMessage(msg, {})
        assert retmessage == msg
        assert retmeta == {}

    def normal_sized_message_with_bad_key(self):
        msg = {
            'category': 'someother',
            'details': {
                'message': {
                    'somekey': 'somevalue'
                }
            }
        }
        (retmessage, retmeta) = self.plugin.onMessage(msg, {})
        assert retmessage == msg
        assert retmeta == {}
