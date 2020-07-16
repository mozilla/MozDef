#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# Copyright (c) 2017 Mozilla Corporation

from mozdef_util.utilities.dot_dict import DotDict
from mozdef_util.query_models import SearchQuery, ExistsMatch

from tests.unit_test_suite import UnitTestSuite

import os
import sys


class TestEsworkerSNSSQS(UnitTestSuite):
    def teardown(self):
        sys.path.remove(self.mq_path)
        super().teardown()

    def setup(self):
        super().setup()
        mq_conn = 'abc'
        task_queue = 'example-logs-mozdef'
        es_connection = self.es_client
        options = DotDict(
            {
                "esbulksize": 0,
                "mozdefhostname": "unittest.hostname",
                "taskexchange": task_queue,
            }
        )
        if 'lib' in sys.modules:
            del sys.modules['lib']
        self.mq_path = os.path.join(os.path.dirname(__file__), "../../mq/")
        sys.path.insert(0, self.mq_path)
        from mq import esworker_sns_sqs
        self.consumer = esworker_sns_sqs.taskConsumer(mq_conn, es_connection, options)

    def search_and_verify_event(self, expected_event):
        self.refresh('events')
        search_query = SearchQuery(minutes=5)
        search_query.add_must(ExistsMatch('tags'))
        results = search_query.execute(self.es_client)
        assert len(results['hits']) == 1
        saved_event = results['hits'][0]['_source']
        self.verify_event(saved_event, expected_event)

    def test_syslog_event(self):
        event = {
            "Type": "Notification",
            "MessageId": "abcdefg",
            "TopicArn": "arn:aws:sns:us-west-2:123456789:example-logs-mozdef",
            "Subject": "Fluentd-Notification",
            "Message": "{\"time\":\"2017-05-25 07:14:15 +0000\",\"timestamp\":\"2017-05-25T07:14:15+00:00\",\"hostname\":\"abcdefghostname\",\"pname\":\"dhclient\",\"processid\":\"[123]\",\"type\":\"syslog\",\"logger\":\"systemslogs\",\"payload\":\"DHCPREQUEST of 1.2.3.4 on eth0 to 5.6.7.8 port 67 (xid=0x123456)\"}",
            "Timestamp": "2017-05-25T07:14:16.103Z",
            "SignatureVersion": "1",
            "Signature": "examplesignatureabcd",
            "SigningCertURL": "https://sns.us-west-2.amazonaws.com/SimpleNotificationService-12345.pem",
            "UnsubscribeURL": "https://sns.us-west-2.amazonaws.com/?Action=Unsubscribe&SubscriptionArn=arn:aws:sns:us-west-2:123456789:example-logs-mozdef:adsf0laser013"
        }
        self.consumer.on_message(event)
        expected_event = {
            'category': 'syslog',
            'details': {'logger': 'systemslogs'},
            'hostname': 'abcdefghostname',
            'mozdefhostname': 'unittest.hostname',
            'processid': '123',
            'processname': 'dhclient',
            'receivedtimestamp': '2017-05-26T17:47:17.813876+00:00',
            'severity': 'INFO',
            'source': 'UNKNOWN',
            'summary': 'DHCPREQUEST of 1.2.3.4 on eth0 to 5.6.7.8 port 67 (xid=0x123456)',
            'tags': ['example-logs-mozdef'],
            'timestamp': '2017-05-25T07:14:15+00:00',
            'utctimestamp': '2017-05-25T07:14:15+00:00',
            'mozdef': {'plugins': []},
            'type': 'event'
        }
        self.search_and_verify_event(expected_event)
