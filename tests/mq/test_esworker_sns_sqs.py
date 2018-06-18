#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
# Copyright (c) 2017 Mozilla Corporation

import json

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

    def test_sso_event(self):
        message_dict = {
            u'category': u'user_feedback',
            u'details': {
                u'action': u'escalate',
                u'alert_information': {
                    u'alert_code': u'12345',
                    u'alert_id': u'abcdefg',
                    u'alert_str_json': u'{"url": "https://www.mozilla.org/alert", "severity": "NOTICE", "tags": ["geomodel"], "utctimestamp": "1976-09-13T07:43:49+00:00", "category": "geomodel", "summary": "christianherring@gmail.com NEWCOUNTRY New York, Mauritania access from 25.141.235.246", "details": {"locality_details": {"city": "New York", "country": "Mauritania"}, "category": "NEWCOUNTRY", "principal": "christianherring@gmail.com", "source_ip": "25.141.235.246"}}',
                    u'date': u'1998-06-24',
                    u'description': u'This alert is created based on geo ip information about the last login of a user.',
                    u'duplicate': False,
                    u'last_update': 1524700512,
                    u'risk': u'high',
                    u'state': u'escalate',
                    u'summary': u'Did you recently login from New York, Mauritania (25.141.235.246)?',
                    u'url': u'https://www.mozilla.org',
                    u'url_title': u'Get Help',
                    u'user_id': u'ad|Mozilla-LDAP-Dev|ttesterson'
                }
            }
        }
        event = {
            u'Message': json.dumps(message_dict),
            u'MessageId': u'123456-248e-5b78-84c5-46ac332ea6cd',
            u'Signature': u'abcdefgh',
            u'SignatureVersion': u'1',
            u'SigningCertURL': u'https://sns.us-west-2.amazonaws.com/SimpleNotificationService-1098765.pem',
            u'Subject': u'sso-dashboard-user-feedback',
            u'Timestamp': u'2018-04-25T23:55:12.854Z',
            u'TopicArn': u'arn:aws:sns:us-west-2:7777777777:SSODashboardAlertFeedback',
            u'Type': u'Notification',
            u'UnsubscribeURL': u'https://sns.us-west-2.amazonaws.com/?Action=Unsubscribe&SubscriptionArn=arn:aws:sns:us-west-2:7777777777:SSODashboardAlertFeedback:123456-248e-5b78-84c5-46ac332ea6cd'
        }
        self.consumer.on_message(event)
        expected_event = {
            u'category': u'user_feedback',
            u'details': {
                u'action': u'escalate',
                u'alert_information': {
                    u'alert_code': u'12345',
                    u'alert_id': u'abcdefg',
                    u'alert_str_json': message_dict['details']['alert_information']['alert_str_json'],
                    u'date': u'1998-06-24',
                    u'description': u'This alert is created based on geo ip information about the last login of a user.',
                    u'duplicate': False,
                    u'last_update': 1524700512,
                    u'risk': u'high',
                    u'state': u'escalate',
                    u'summary': u'Did you recently login from New York, Mauritania (25.141.235.246)?',
                    u'url': u'https://www.mozilla.org',
                    u'url_title': u'Get Help',
                    u'user_id': u'ad|Mozilla-LDAP-Dev|ttesterson'
                }
            },
            u'hostname': u'UNKNOWN',
            u'mozdefhostname': u'unittest.hostname',
            u'processid': u'UNKNOWN',
            u'processname': u'UNKNOWN',
            u'receivedtimestamp': u'2018-04-26T00:11:23.479565+00:00',
            u'severity': u'INFO',
            u'source': u'UNKNOWN',
            u'summary': u'UNKNOWN',
            u'tags': [u'example-logs-mozdef'],
            u'timestamp': u'2018-04-26T00:11:23.479771+00:00',
            u'utctimestamp': u'2018-04-26T00:11:23.479771+00:00'
        }
        self.search_and_verify_event(expected_event)
