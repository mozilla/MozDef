# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
# Copyright (c) 2017 Mozilla Corporation

import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), "../../../mq/plugins"))
from cloudtrail import message


class TestCloudtrailPlugin():
    def setup(self):
        self.plugin = message()

    def test_nonexistent_source(self):
        msg = {
            'category': 'someother',
        }
        (retmessage, retmeta) = self.plugin.onMessage(msg, {})
        assert retmessage == msg
        assert retmeta == {}

    def test_incorrect_source(self):
        msg = {
            'source': 'someother',
        }
        (retmessage, retmeta) = self.plugin.onMessage(msg, {})
        assert retmessage == msg
        assert retmeta == {}

    def test_iamInstanceProfile(self):
        msg = {
            'source': 'cloudtrail',
            'details': {
                'requestparameters': {
                    'iamInstanceProfile': 'astringvalue',
                }
            }
        }
        (retmessage, retmeta) = self.plugin.onMessage(msg, {})

        expected_message = {
            'source': 'cloudtrail',
            'details': {
                'requestparameters': {
                    'iamInstanceProfile': {
                        'raw_value': 'astringvalue',
                    }
                }
            }
        }
        assert retmessage == expected_message
        assert retmeta == {}

    def test_attribute(self):
        msg = {
            'source': 'cloudtrail',
            'details': {
                'requestparameters': {
                    'attribute': 'astringvalue',
                }
            }
        }
        (retmessage, retmeta) = self.plugin.onMessage(msg, {})

        expected_message = {
            'source': 'cloudtrail',
            'details': {
                'requestparameters': {
                    'attribute': {
                        'raw_value': 'astringvalue',
                    }
                }
            }
        }
        assert retmessage == expected_message
        assert retmeta == {}
