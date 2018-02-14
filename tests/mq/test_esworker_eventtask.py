#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
# Copyright (c) 2017 Mozilla Corporation

import pytz
import tzlocal
import datetime


def utc_timezone():
    return pytz.timezone('UTC')

tzlocal.get_localzone = utc_timezone


import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), "../../mq"))
from mq import esworker_eventtask


class MockOptions():
    @property
    def mozdefhostname(self):
        return 'sample'


class TestKeyMapping():
    def setup(self):
        mock_options = MockOptions()
        esworker_eventtask.options = mock_options
        self.key_mapping = esworker_eventtask.keyMapping

    def test_syslog_dict(self):
        syslog_dict = {
            u'CATEGORY': 'syslog',
            u'DATE': u'Oct 27 14:01:12',
            u'FACILITY': u'daemon',
            u'HOST': u'ub_server',
            u'HOST_FROM': u'10.1.20.139',
            u'LEGACY_MSGHDR': u'systemd[1]: ',
            u'MESSAGE': u'Stopped Getty on tty1.',
            u'PID': u'1',
            u'PRIORITY': u'info',
            u'PROGRAM': u'systemd',
            u'SEQNUM': u'8',
            u'SOURCE': u'syslog_tcp',
            u'SOURCEIP': u'10.1.20.139',
            u'TAGS': u'.source.syslog_tcp'
        }

        result = self.key_mapping(syslog_dict)
        assert result['processid'] == '1'
        assert result['processname'] == 'systemd'
        assert result['severity'] == 'INFO'
        assert result['mozdefhostname'] == 'sample'
        assert result['hostname'] == 'ub_server'
        assert result['summary'] == 'Stopped Getty on tty1.'
        assert result['source'] == 'daemon'
        assert result['receivedtimestamp'] != result['utctimestamp']
        expected_year = datetime.datetime.now().year
        assert result['utctimestamp'] == str(expected_year) + '-10-27T14:01:12+00:00'
        assert result['timestamp'] == str(expected_year) + '-10-27T14:01:12+00:00'
        assert result['details']['sourceipaddress'] == '10.1.20.139'
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
        assert result['details'].keys() == ['message', 'payload']
        assert result['details']['message'] == 'somestring'
        assert result['details']['payload'] == 'examplepayload'

    def test_no_details(self):
        message = {
            'summary': 'example summary',
        }
        result = self.key_mapping(message)
        assert result['details'] == {}
