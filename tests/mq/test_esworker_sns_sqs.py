#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
# Copyright (c) 2017 Mozilla Corporation


import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), "../../mq"))
from mq.esworker_sns_sqs import taskConsumer

sys.path.append(os.path.join(os.path.dirname(__file__), "../../lib"))
from utilities.dot_dict import DotDict
from query_models import SearchQuery, ExistsMatch

sys.path.append(os.path.join(os.path.dirname(__file__), "../"))
from unit_test_suite import UnitTestSuite


class TestEsworkerSNSSQS(UnitTestSuite):
    def setup(self):
        super(TestEsworkerSNSSQS, self).setup()
        mq_conn = 'abc'
        task_queue = 'example-logs-mozdef'
        es_connection = self.es_client
        options = DotDict(
            {
                "esbulksize": 0,
                "mozdefhostname": "unittest.hostname",
                "taskexchange": task_queue,
                'plugincheckfrequency': 120,
            }
        )
        self.consumer = taskConsumer(mq_conn, task_queue, es_connection, options)

    def search_and_verify_event(self, expected_event):
        self.flush('events')
        search_query = SearchQuery(minutes=5)
        search_query.add_must(ExistsMatch('tags'))
        results = search_query.execute(self.es_client)
        assert len(results['hits']) == 1
        saved_event = results['hits'][0]['_source']
        self.verify_event(saved_event, expected_event)

    def test_event1(self):
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
            u'category': u'syslog',
            u'details': {u'logger': u'systemslogs'},
            u'hostname': u'abcdefghostname',
            u'mozdefhostname': u'unittest.hostname',
            u'processid': u'123',
            u'processname': u'dhclient',
            u'receivedtimestamp': u'2017-05-26T17:47:17.813876+00:00',
            u'severity': u'INFO',
            u'source': u'UNKNOWN',
            u'summary': u'DHCPREQUEST of 1.2.3.4 on eth0 to 5.6.7.8 port 67 (xid=0x123456)',
            u'tags': [u'example-logs-mozdef'],
            u'timestamp': u'2017-05-25T07:14:15+00:00',
            u'utctimestamp': u'2017-05-25T07:14:15+00:00'
        }
        self.search_and_verify_event(expected_event)
