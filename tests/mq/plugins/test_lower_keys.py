# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# Copyright (c) 2017 Mozilla Corporation

from mq.plugins.lower_keys import message


class TestLowerKeysPlugin():
    def setup(self):
        self.plugin = message()

    def test_uppercase_details(self):
        msg = {
            'source': 'cloudtrail',
            'Details': {
                'requestparameters': {
                    'description': 'astringvalue',
                }
            }
        }
        (retmessage, retmeta) = self.plugin.onMessage(msg, {})

        expected_message = {
            'source': 'cloudtrail',
            'details': {
                'requestparameters': {
                    'description': 'astringvalue',
                }
            }
        }
        assert retmessage == expected_message
        assert retmeta == {}

    def test_uppercase_nested_keys(self):
        msg = {
            'source': 'cloudtrail',
            'details': {
                'RequestParameters': {
                    'Description': 'astringvalue',
                }
            }
        }
        (retmessage, retmeta) = self.plugin.onMessage(msg, {})

        expected_message = {
            'source': 'cloudtrail',
            'details': {
                'requestparameters': {
                    'description': 'astringvalue',
                }
            }
        }
        assert retmessage == expected_message
        assert retmeta == {}

    def test_uppercase_nested_keys2(self):
        msg = {
            'source': 'cloudtrail',
            'details': {
                'RequestParameters': {
                    'Description': 'astringvalue',
                    'ApplicationSource': {
                        'someKey:': 'anothervalue',
                    }
                }
            }
        }
        (retmessage, retmeta) = self.plugin.onMessage(msg, {})

        expected_message = {
            'source': 'cloudtrail',
            'details': {
                'requestparameters': {
                    'description': 'astringvalue',
                    'applicationsource': {
                        'somekey:': 'anothervalue',
                    }
                }
            }
        }
        assert retmessage == expected_message
        assert retmeta == {}
