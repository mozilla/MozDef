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
            'summary': 'zoom_event',
            'source': 'api_aws_lambda',
            'hostname': 'zoom_host',
            'details': {
                'event': 'meeting.ended',
                'payload': {
                    'object': {
                        'topic': 'zoomroom',
                        'account_id': 'ABCDEFG123456',
                        'id': '123456789',
                        'type': '4',
                        'uuid': 'aodij/OWIE9241048='
                    }
                }
            }
        }
        (retmessage, retmeta) = self.plugin.onMessage(msg, {})

        expected_message = {
            'summary': 'zoom: meeting.ended',
            'source': 'api_aws_lambda',
            'hostname': 'zoom_host',
            'details': {
                'event': 'meeting.ended',
                'payload': {
                    'object': {
                        'account_id': 'ABCDEFG123456',
                        'id': '123456789',
                        'type': '4',
                        'uuid': 'aodij/OWIE9241048='
                    }
                }
            }
        }
        assert retmessage == expected_message
        assert retmeta == {}

    def test_summary_user_name(self):
        msg = {
            'summary': 'zoom_event',
            'source': 'api_aws_lambda',
            'hostname': 'zoom_host',
            'details': {
                'event': 'meeting.sharing_ended',
                'payload': {
                    'object': {
                        'topic': 'zoomroom',
                        'account_id': 'ABCDEFG123456',
                        'id': '123456789',
                        'type': '4',
                        'uuid': 'aodij/OWIE9241048=',
                        "participant": {
                            'user_id': '12039103',
                            'user_name': 'Random User',
                        }
                    }
                }
            }
        }
        (retmessage, retmeta) = self.plugin.onMessage(msg, {})

        expected_message = {
            'summary': 'zoom: meeting.sharing_ended triggered by user Random User',
            'source': 'api_aws_lambda',
            'hostname': 'zoom_host',
            'details': {
                'event': 'meeting.sharing_ended',
                'payload': {
                    'object': {
                        'account_id': 'ABCDEFG123456',
                        'id': '123456789',
                        'type': '4',
                        'uuid': 'aodij/OWIE9241048=',
                        "participant": {
                            'user_id': '12039103',
                            'user_name': 'Random User',
                        }
                    }
                }
            }
        }
        assert retmessage == expected_message
        assert retmeta == {}

    def test_summary_operator(self):
        msg = {
            'summary': 'zoom_event',
            'source': 'api_aws_lambda',
            'hostname': 'zoom_host',
            'details': {
                'event': 'meeting.created',
                'payload': {
                    'account_id': 'ABCDEFG123456',
                    'operator': 'randomuser@randomco.com',
                    'operator_id': '12o3i-294jo24jad',
                    'object': {
                        'id': '123456789',
                        'type': '2',
                        'uuid': 'aodij/OWIE9241048=',
                    }
                }
            }
        }
        (retmessage, retmeta) = self.plugin.onMessage(msg, {})

        expected_message = {
            'summary': 'zoom: meeting.created triggered by user randomuser@randomco.com',
            'source': 'api_aws_lambda',
            'hostname': 'zoom_host',
            'details': {
                'event': 'meeting.created',
                'payload': {
                    'account_id': 'ABCDEFG123456',
                    'operator': 'randomuser@randomco.com',
                    'operator_id': '12o3i-294jo24jad',
                    'object': {
                        'id': '123456789',
                        'type': '2',
                        'uuid': 'aodij/OWIE9241048=',
                    }
                }
            }
        }
        assert retmessage == expected_message
        assert retmeta == {}

    def test_remove_duplicate_account_id(self):
        msg = {
            'summary': 'zoom_event',
            'source': 'api_aws_lambda',
            'hostname': 'zoom_host',
            'details': {
                'event': 'meeting.created',
                'payload': {
                    'account_id': 'ABCDEFG123456',
                    'object': {
                        'account_id': 'ABCDEFG123456',
                        'id': '123456789',
                        'type': '2',
                        'uuid': 'aodij/OWIE9241048='
                    }
                }
            }
        }
        (retmessage, retmeta) = self.plugin.onMessage(msg, {})

        expected_message = {
            'summary': 'zoom: meeting.created',
            'source': 'api_aws_lambda',
            'hostname': 'zoom_host',
            'details': {
                'event': 'meeting.created',
                'payload': {
                    'account_id': 'ABCDEFG123456',
                    'object': {
                        'id': '123456789',
                        'type': '2',
                        'uuid': 'aodij/OWIE9241048='
                    }
                }
            }
        }
        assert retmessage == expected_message
        assert retmeta == {}
