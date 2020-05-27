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
            'category': 'zoom',
            'severity': 'info',
            'eventsource': 'MozDef-EF-zoom',
            'tags': 'zoom',
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
            'category': 'zoom',
            'severity': 'info',
            'processname': 'zoom_webhook_api',
            'eventsource': 'MozDef-EF-zoom',
            'tags': 'zoom',
            'details': {
                'event': 'meeting.ended',
                'account_id': 'ABCDEFG123456',
                'id': '123456789',
                'type': '4',
                'uuid': 'aodij/OWIE9241048='
            }
        }
        assert retmessage == expected_message
        assert retmeta == {}

    def test_summary_user_name(self):
        msg = {
            'summary': 'zoom_event',
            'source': 'api_aws_lambda',
            'hostname': 'zoom_host',
            'category': 'zoom',
            'severity': 'info',
            'eventsource': 'MozDef-EF-zoom',
            'tags': 'zoom',
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
                            'user_name': 'Random User'
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
            'category': 'zoom',
            'severity': 'info',
            'processname': 'zoom_webhook_api',
            'eventsource': 'MozDef-EF-zoom',
            'tags': 'zoom',
            'details': {
                'event': 'meeting.sharing_ended',
                'account_id': 'ABCDEFG123456',
                'id': '123456789',
                'type': '4',
                'uuid': 'aodij/OWIE9241048=',
                'participant_username': 'Random User',
                'participant_user_id': '12039103'
            }
        }
        assert retmessage == expected_message
        assert retmeta == {}

    def test_summary_operator(self):
        msg = {
            'summary': 'zoom_event',
            'source': 'api_aws_lambda',
            'hostname': 'zoom_host',
            'category': 'zoom',
            'severity': 'info',
            'eventsource': 'MozDef-EF-zoom',
            'tags': 'zoom',
            'details': {
                'event': 'meeting.created',
                'payload': {
                    'account_id': 'ABCDEFG123456',
                    'operator': 'randomuser@randomco.com',
                    'operator_id': '12o3i-294jo24jad',
                    'object': {
                        'id': '123456789',
                        'type': '2',
                        'uuid': 'aodij/OWIE9241048='
                    }
                }
            }
        }
        (retmessage, retmeta) = self.plugin.onMessage(msg, {})

        expected_message = {
            'summary': 'zoom: meeting.created triggered by user randomuser@randomco.com',
            'source': 'api_aws_lambda',
            'hostname': 'zoom_host',
            'category': 'zoom',
            'severity': 'info',
            'processname': 'zoom_webhook_api',
            'eventsource': 'MozDef-EF-zoom',
            'tags': 'zoom',
            'details': {
                'account_id': 'ABCDEFG123456',
                'event': 'meeting.created',
                'id': '123456789',
                'type': '2',
                'user_id': '12o3i-294jo24jad',
                'username': 'randomuser@randomco.com',
                'uuid': 'aodij/OWIE9241048='
            }
        }
        assert retmessage == expected_message
        assert retmeta == {}

    def test_remove_duplicate_account_id(self):
        msg = {
            'summary': 'zoom_event',
            'source': 'api_aws_lambda',
            'hostname': 'zoom_host',
            'severity': 'info',
            'processname': 'zoom_webhook_api',
            'eventsource': 'MozDef-EF-zoom',
            'tags': 'zoom',
            'category': 'zoom',
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
            'category': 'zoom',
            'source': 'api_aws_lambda',
            'hostname': 'zoom_host',
            'severity': 'info',
            'processname': 'zoom_webhook_api',
            'eventsource': 'MozDef-EF-zoom',
            'tags': 'zoom',
            'details': {
                'event': 'meeting.created',
                'account_id': 'ABCDEFG123456',
                'id': '123456789',
                'type': '2',
                'uuid': 'aodij/OWIE9241048='

            }
        }
        assert retmessage == expected_message
        assert retmeta == {}

    def test_differing_account_ids(self):
        msg = {
            'summary': 'zoom_event',
            'source': 'api_aws_lambda',
            'hostname': 'zoom_host',
            'severity': 'info',
            'eventsource': 'MozDef-EF-zoom',
            'tags': 'zoom',
            'category': 'zoom',
            'details': {
                'event': 'meeting.created',
                'payload': {
                    'account_id': 'ABCDEFG123456',
                    'object': {
                        'account_id': 'HIJKLMN123456',
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
            'category': 'zoom',
            'source': 'api_aws_lambda',
            'hostname': 'zoom_host',
            'severity': 'info',
            'eventsource': 'MozDef-EF-zoom',
            'tags': 'zoom',
            'processname': 'zoom_webhook_api',
            'details': {
                'event': 'meeting.created',
                'account_id': 'ABCDEFG123456',
                'id': '123456789',
                'type': '2',
                'uuid': 'aodij/OWIE9241048='
            }
        }
        assert retmessage == expected_message
        assert retmeta == {}

    def test_multiple_tags_check(self):
        msg = {
            'summary': 'zoom_event',
            'source': 'api_aws_lambda',
            'hostname': 'zoom_host',
            'severity': 'info',
            'eventsource': 'MozDef-EF-zoom',
            'tags': ['zoom', 'MozDef-EF-zoom-dev'],
            'category': 'zoom',
            'details': {
                'event': 'meeting.created',
                'payload': {
                    'account_id': 'ABCDEFG123456',
                    'object': {
                        'account_id': 'HIJKLMN123456',
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
            'category': 'zoom',
            'source': 'api_aws_lambda',
            'hostname': 'zoom_host',
            'severity': 'info',
            'eventsource': 'MozDef-EF-zoom',
            'tags': ['zoom', 'MozDef-EF-zoom-dev'],
            'processname': 'zoom_webhook_api',
            'details': {
                'account_id': 'ABCDEFG123456',
                'event': 'meeting.created',
                'id': '123456789',
                'type': '2',
                'uuid': 'aodij/OWIE9241048='
            }
        }
        assert retmessage == expected_message
        assert retmeta == {}

    def test_start_time_empty_string(self):
        msg = {
            'summary': 'zoom_event',
            'source': 'api_aws_lambda',
            'hostname': 'zoom_host',
            'severity': 'info',
            'eventsource': 'MozDef-EF-zoom',
            'tags': ['zoom', 'MozDef-EF-zoom-dev'],
            'category': 'zoom',
            'details': {
                'event': 'meeting.created',
                'payload': {
                    'account_id': 'ABCDEFG123456',
                    'object': {
                        'account_id': 'ABCDEFG123456',
                        'id': '123456789',
                        'type': '2',
                        'uuid': 'aodij/OWIE9241048=',
                        'start_time': ''
                    },
                    'old_object': {
                        'start_time': '2020-02-11T20:25:30Z',
                        'duration': '60'
                    }
                }
            }
        }
        (retmessage, retmeta) = self.plugin.onMessage(msg, {})

        expected_message = {
            'summary': 'zoom: meeting.created',
            'category': 'zoom',
            'source': 'api_aws_lambda',
            'hostname': 'zoom_host',
            'severity': 'info',
            'eventsource': 'MozDef-EF-zoom',
            'tags': ['zoom', 'MozDef-EF-zoom-dev'],
            'processname': 'zoom_webhook_api',
            'details': {
                'account_id': 'ABCDEFG123456',
                'event': 'meeting.created',
                'id': '123456789',
                'type': '2',
                'uuid': 'aodij/OWIE9241048=',
                'original_sched_start_time': '2020-02-11T20:25:30Z',
                'original_sched_duration': '60'
            }
        }
        assert retmessage == expected_message
        assert retmeta == {}

    def test_empty_original_sched_start_time_strings(self):
        msg = {
            'summary': 'zoom_event',
            'source': 'api_aws_lambda',
            'hostname': 'zoom_host',
            'severity': 'info',
            'eventsource': 'MozDef-EF-zoom',
            'tags': ['zoom', 'MozDef-EF-zoom-dev'],
            'category': 'zoom',
            'details': {
                'event': 'meeting.updated',
                'payload': {
                    'account_id': 'ABCDEFG123456',
                    'object': {
                        'account_id': 'ABCDEFG123456',
                        'id': '123456789',
                        'type': '2',
                        'uuid': 'aodij/OWIE9241048=',
                        'start_time': ''
                    },
                    'old_object': {
                        'id': '123456789',
                        'type': '2',
                        'start_time': '',
                        'duration': '60'
                    }
                }
            }
        }
        (retmessage, retmeta) = self.plugin.onMessage(msg, {})

        expected_message = {
            'summary': 'zoom: meeting.updated',
            'category': 'zoom',
            'source': 'api_aws_lambda',
            'hostname': 'zoom_host',
            'severity': 'info',
            'eventsource': 'MozDef-EF-zoom',
            'tags': ['zoom', 'MozDef-EF-zoom-dev'],
            'processname': 'zoom_webhook_api',
            'details': {
                'account_id': 'ABCDEFG123456',
                'event': 'meeting.updated',
                'id': '123456789',
                'type': '2',
                'uuid': 'aodij/OWIE9241048=',
                'original_sched_duration': '60'
            }
        }
        assert retmessage == expected_message
        assert retmeta == {}

    def test_recording_file_end_empty_string(self):
        msg = {
            'summary': 'zoom_event',
            'source': 'api_aws_lambda',
            'hostname': 'zoom_host',
            'severity': 'info',
            'eventsource': 'MozDef-EF-zoom',
            'tags': ['zoom', 'MozDef-EF-zoom-dev'],
            'category': 'zoom',
            'details': {
                'event': 'recording.paused',
                'payload': {
                    'account_id': 'ABCDEFG123456',
                    'object': {
                        'account_id': 'ABCDEFG123456',
                        'id': '123456789',
                        'type': '2',
                        'uuid': 'aodij/OWIE9241048=',
                        'recording_file': {
                            'recording_end': ''
                        }
                    },
                    'old_object': {
                        'start_time': '2020-02-11T20:25:30Z',
                        'duration': '60'
                    }
                }
            }
        }
        (retmessage, retmeta) = self.plugin.onMessage(msg, {})

        expected_message = {
            'summary': 'zoom: recording.paused',
            'category': 'zoom',
            'source': 'api_aws_lambda',
            'hostname': 'zoom_host',
            'severity': 'info',
            'eventsource': 'MozDef-EF-zoom',
            'tags': ['zoom', 'MozDef-EF-zoom-dev'],
            'processname': 'zoom_webhook_api',
            'details': {
                'account_id': 'ABCDEFG123456',
                'event': 'recording.paused',
                'id': '123456789',
                'type': '2',
                'uuid': 'aodij/OWIE9241048=',
                'original_sched_start_time': '2020-02-11T20:25:30Z',
                'original_sched_duration': '60'
            }
        }
        assert retmessage == expected_message
        assert retmeta == {}

    def test_remove_old_topic_string(self):
        msg = {
            'summary': 'zoom_event',
            'source': 'api_aws_lambda',
            'hostname': 'zoom_host',
            'severity': 'info',
            'eventsource': 'MozDef-EF-zoom',
            'tags': ['zoom', 'MozDef-EF-zoom-dev'],
            'category': 'zoom',
            'details': {
                'event': 'meeting.updated',
                'payload': {
                    'account_id': 'ABCDEFG123456',
                    'object': {
                        'account_id': 'ABCDEFG123456',
                        'id': '123456789',
                        'type': '2',
                        'uuid': 'aodij/OWIE9241048='
                    },
                    'old_object': {
                        'topic': 'my secret meeting',
                        'duration': '60'
                    }
                }
            }
        }
        (retmessage, retmeta) = self.plugin.onMessage(msg, {})

        expected_message = {
            'summary': 'zoom: meeting.updated',
            'category': 'zoom',
            'source': 'api_aws_lambda',
            'hostname': 'zoom_host',
            'severity': 'info',
            'eventsource': 'MozDef-EF-zoom',
            'tags': ['zoom', 'MozDef-EF-zoom-dev'],
            'processname': 'zoom_webhook_api',
            'details': {
                'account_id': 'ABCDEFG123456',
                'event': 'meeting.updated',
                'id': '123456789',
                'type': '2',
                'uuid': 'aodij/OWIE9241048=',
                'original_sched_duration': '60'
            }
        }
        assert retmessage == expected_message
        assert retmeta == {}
