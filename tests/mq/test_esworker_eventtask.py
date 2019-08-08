#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# Copyright (c) 2017 Mozilla Corporation

import pytz
import tzlocal
import datetime
import os
import sys


def utc_timezone():
    return pytz.timezone('UTC')


tzlocal.get_localzone = utc_timezone


class MockOptions():
    @property
    def mozdefhostname(self):
        return 'sample'


class TestKeyMapping():
    def teardown(self):
        sys.path.remove(self.mq_path)

    def setup(self):
        if 'lib' in sys.modules:
            del sys.modules['lib']
        self.mq_path = os.path.join(os.path.dirname(__file__), "../../mq/")
        sys.path.insert(0, self.mq_path)
        from mq import esworker_eventtask
        mock_options = MockOptions()
        esworker_eventtask.options = mock_options
        self.key_mapping = esworker_eventtask.keyMapping

    def test_syslog_dict(self):
        syslog_dict = {
            'CATEGORY': 'syslog',
            'DATE': 'Oct 27 14:01:12',
            'FACILITY': 'daemon',
            'HOST': 'ub_server',
            'HOST_FROM': '10.1.20.139',
            'LEGACY_MSGHDR': 'systemd[1]: ',
            'MESSAGE': 'Stopped Getty on tty1.',
            'PID': '1',
            'PRIORITY': 'info',
            'PROGRAM': 'systemd',
            'SEQNUM': '8',
            'SOURCE': 'syslog_tcp',
            'SOURCEIP': '10.1.20.139',
            'TAGS': '.source.syslog_tcp'
        }

        result = self.key_mapping(syslog_dict)
        assert result['processid'] == '1'
        assert result['processname'] == 'systemd'
        assert result['severity'] == 'INFO'
        assert result['mozdefhostname'] == 'sample'
        assert result['hostname'] == 'ub_server'
        assert result['summary'] == 'Stopped Getty on tty1.'
        assert result['source'] == 'syslog_tcp'
        assert result['receivedtimestamp'] != result['utctimestamp']
        expected_year = datetime.datetime.now().year
        assert result['utctimestamp'] == str(expected_year) + '-10-27T14:01:12+00:00'
        assert result['timestamp'] == str(expected_year) + '-10-27T14:01:12+00:00'
        assert result['details']['eventsourceipaddress'] == '10.1.20.139'
        assert result['tags'] == ['.source.syslog_tcp']
        assert result['category'] == 'syslog'

    def test_tags_list(self):
        tags_dict = {
            'tags': ['example1']
        }
        result = self.key_mapping(tags_dict)
        assert result['tags'] == ['example1']

    def test_details_nondict(self):
        message = {
            'summary': 'example summary',
            'payload': 'examplepayload',
            'details': 'somestring',
        }
        result = self.key_mapping(message)
        assert result['summary'] == 'example summary'
        assert sorted(result['details'].keys()) == ['message', 'payload']
        assert result['details']['message'] == 'somestring'
        assert result['details']['payload'] == 'examplepayload'

    def test_no_details(self):
        message = {
            'summary': 'example summary',
        }
        result = self.key_mapping(message)
        assert result['details'] == {}
