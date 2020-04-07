# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# Copyright (c) 2017 Mozilla Corporation

import json

from .positive_alert_test_case import PositiveAlertTestCase
from .negative_alert_test_case import NegativeAlertTestCase

from .alert_test_suite import AlertTestSuite


class TestAlertFeedbackEvents(AlertTestSuite):
    inner_alert_dict = {
        "summary": "ttesterson@gmail.com NEWCOUNTRY Montana, Tonga access from 109.117.1.33",
        "utctimestamp": "2010-04-01T20:49:15+00:00",
        "url": "https://www.mozilla.org/alert",
        "category": "geomodel",
        "severity": "NOTICE",
        "details": {
            "locality_details": {
                "country": "Tonga",
                "city": "Montana"
            },
            "principal": "ttesterson@gmail.com",
            "source_ip": "109.117.1.33",
            "category": "NEWCOUNTRY"
        },
        "tags": ["geomodel"]
    }
    default_event = {
        "_source": {
            'category': 'user_feedback',
            'details': {
                'action': 'escalate',
                'alert_information': {
                    'alert_code': '123456',
                    'alert_id': '7891011',
                    'alert_str_json': json.dumps(inner_alert_dict),
                    'date': '2012-06-15',
                    'description': 'This alert is created based on geo ip information about the last login of a user.',
                    'duplicate': False,
                    'last_update': 1524686938,
                    'risk': 'high',
                    'state': 'escalate',
                    'summary': 'Did you recently login from Montana, Tonga (109.117.1.33)?',
                    'url': 'https://www.mozilla.org',
                    'url_title': 'Get Help',
                    'user_id': 'ad|Mozilla|ttesterson'
                }
            },
            'mozdefhostname': 'host1',
            'severity': 'INFO',
            'summary': 'Did you recently login from Montana, Tonga (109.117.1.33)?',
            'tags': ['SSODashboardAlertFeedback']
        }
    }

    default_alert = {
        "category": "user_feedback",
        "tags": ['user_feedback', 'customtag1'],
        "severity": "NOTICE",
        "summary": "ad|Mozilla|ttesterson escalated alert within single-sign on (SSO) dashboard. Event Date: 2012-06-15 Summary: \"Did you recently login from Montana, Tonga (109.117.1.33)?\"",
    }

    test_cases = []
    test_cases.append(
        PositiveAlertTestCase(
            description="Positive test case with good event",
            events=[AlertTestSuite.create_event(default_event)],
            expected_alert=default_alert
        )
    )

    event = AlertTestSuite.create_event(default_event)
    event['_source']['details']['alert_information']['alert_code'] = '7891011'
    alert = AlertTestSuite.create_alert(default_alert)
    alert['tags'] = ['user_feedback', 'customtag2']
    test_cases.append(
        PositiveAlertTestCase(
            description="Positive test case with good event",
            events=[event],
            expected_alert=alert
        )
    )

    unicode_event = AlertTestSuite.create_event(default_event)
    unicode_event['_source']['details']['alert_information']['user_id'] = '\xfctest'
    unicode_alert = AlertTestSuite.create_alert(default_alert)
    unicode_alert['summary'] = '\xfctest escalated alert within single-sign on (SSO) dashboard. Event Date: 2012-06-15 Summary: "Did you recently login from Montana, Tonga (109.117.1.33)?"'
    test_cases.append(
        PositiveAlertTestCase(
            description="Positive test case with good unicode event",
            events=[unicode_event],
            expected_alert=unicode_alert
        )
    )

    event = AlertTestSuite.create_event(default_event)
    event['_source']['utctimestamp'] = AlertTestSuite.subtract_from_timestamp_lambda({'minutes': 31})
    event['_source']['receivedtimestamp'] = AlertTestSuite.subtract_from_timestamp_lambda({'minutes': 31})
    test_cases.append(
        NegativeAlertTestCase(
            description="Negative test case with an event with old timestamp",
            events=[event],
        )
    )

    event = AlertTestSuite.create_event(default_event)
    event['_source']['category'] = 'badcategory'
    test_cases.append(
        NegativeAlertTestCase(
            description="Negative test case with an event with bad category",
            events=[event],
        )
    )

    event = AlertTestSuite.create_event(default_event)
    event['_source']['details']['action'] = 'badaction'
    test_cases.append(
        NegativeAlertTestCase(
            description="Negative test case with an event with bad action",
            events=[event],
        )
    )
