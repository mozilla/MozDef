# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# Copyright (c) 2017 Mozilla Corporation

from mq.plugins.zoom_fixup import message


class TestZoomFixupPlugin():
    def setup(self):
        self.plugin = message()

    def test_topic_removal(self):
        msg = {
            'source': 'api_aws_lambda',
            'details': {
                'event': 'meeting.ended',
                'payload': {
                    'object': {
                        'topic': 'zoomroom',
                        'account_id': 'ABCDEFG123456',
                        'id': '123456789',
                        'type': '4'
                        'uuid': 'aodij/OWIE9241048=',
                    }
                }
            }
        }
        (retmessage, retmeta) = self.plugin.onMessage(msg, {})

        expected_message = {
            'source': 'api_aws_lambda',
            'details': {
                'event': 'meeting.ended',
                'payload': {
                    'object': {
                        'account_id': 'ABCDEFG123456',
                        'id': '123456789',
                        'type': '4'
                        'uuid': 'aodij/OWIE9241048=',
                    }
                }
            }
        }
        assert retmessage == expected_message
        assert retmeta == {}
