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

    def test_nonexistent_category(self):
        msg = {
            'source': 'someother',
        }
        (retmessage, retmeta) = self.plugin.onMessage(msg, {})
        assert retmessage == msg
        assert retmeta == {}

    def test_incorrect_category(self):
        msg = {
            'category': 'someother',
        }
        (retmessage, retmeta) = self.plugin.onMessage(msg, {})
        assert retmessage == msg
        assert retmeta == {}

    def test_iamInstanceProfile(self):
        msg = {
            'category': 'cloudtrail',
            'details': {
                'requestparameters': {
                    'iamInstanceProfile': 'astringvalue',
                }
            }
        }
        (retmessage, retmeta) = self.plugin.onMessage(msg, {})

        expected_message = {
            'category': 'cloudtrail',
            'details': {
                'requestparameters': {
                    'iamInstanceProfile': {
                        'name': 'astringvalue',
                    }
                }
            }
        }
        assert retmessage == expected_message
        assert retmeta == {}

    def test_attribute(self):
        msg = {
            'category': 'cloudtrail',
            'details': {
                'requestparameters': {
                    'attribute': 'astringvalue',
                }
            }
        }
        (retmessage, retmeta) = self.plugin.onMessage(msg, {})

        expected_message = {
            'category': 'cloudtrail',
            'details': {
                'requestparameters': {
                    'attribute': {
                        'name': 'astringvalue',
                    }
                }
            }
        }
        assert retmessage == expected_message
        assert retmeta == {}
