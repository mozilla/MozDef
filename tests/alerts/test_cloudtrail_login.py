# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
# Copyright (c) 2017 Mozilla Corporation
from positive_alert_test_case import PositiveAlertTestCase
from negative_alert_test_case import NegativeAlertTestCase
from alert_test_suite import AlertTestSuite


class TestCloudtrailLogin(AlertTestSuite):
    alert_filename = "cloudtrail_login"
    alert_classname = "AlertCloudtrailLogin"

    default_event = {
        "_source": {
            "category": "AwsConsoleSignIn",
            "hostname": "signin.amazonaws.com",
            "summary": "1.2.3.4 performed ConsoleLogin in signin.amazonaws.com",
            "details": {
                "eventname": "ConsoleLogin",
                "useridentity": {
                    "username": "randomuser",
                    "type": "IAMUser",
                },
                "sourceipaddress": "1.2.3.4",
                "responseelements": {
                    "consolelogin": "Success",
                },
            },
            "type": "cloudtrail",
            "tags": ['cloudtrail'],
        }
    }

    # This event is an alternate source that we'd want to aggregate
    default_event2 = AlertTestSuite.copy(default_event)
    default_event2["_source"]["details"]["sourceipaddress"] = "10.1.1.2"
    default_event2["_source"]["summary"] = "10.1.1.2 performed ConsoleLogin in signin.amazonaws.com"

    # This alert is the expected result from running this task
    default_alert = {
        "category": "authentication",
        "tags": ['cloudtrail'],
        "severity": "NOTICE",
        "summary": 'Cloudtrail Event: Multiple successful logins for ramdomuser from 1.2.3.4',
    }

    default_alert_aggregated = AlertTestSuite.copy(default_alert)
    default_alert_aggregated["summary"] = 'Cloudtrail Event: Multiple successful logins for randomuser from 1.2.3.4,10.1.1.2'

    test_cases = []

    test_cases.append(
        PositiveAlertTestCase(
            description="Positive test with default events and default alert expected",
            events=AlertTestSuite.create_events(default_event, 10),
            expected_alert=default_alert
        )
    )

    events = AlertTestSuite.create_events(default_event, 10)
    for event in events:
        event['_source']['category'] = 'bad'
    test_cases.append(
        NegativeAlertTestCase(
            description="Negative test case with events with incorrect category",
            events=events,
        )
    )

    events = AlertTestSuite.create_events(default_event, 10)
    for event in events:
        event['_source']['details']['useridentity']['username'] = 'HIDDEN_DUE_TO_SECURITY_REASONS'
    test_cases.append(
        NegativeAlertTestCase(
            description="Negative test case with events with incorrect details.useridentity.username",
            events=events,
        )
    )

    events = AlertTestSuite.create_events(default_event, 10)
    for event in events:
        event['_source']['details']['type'] = None
    test_cases.append(
        NegativeAlertTestCase(
            description="Negative test case with events with non-existent details.type",
            events=events,
        )
    )

    events = AlertTestSuite.create_events(default_event, 10)
    for event in events:
        event['_source']['utctimestamp'] = AlertTestSuite.subtract_from_timestamp_lambda(date_timedelta={'minutes': 21})
        event['_source']['receivedtimestamp'] = AlertTestSuite.subtract_from_timestamp_lambda(date_timedelta={'minutes': 21})
    test_cases.append(
        NegativeAlertTestCase(
            description="Negative test case with old timestamp",
            events=events,
        )
    )

    events1 = AlertTestSuite.create_events(default_event, 10)
    events2 = AlertTestSuite.create_events(default_event2, 10)
    test_cases.append(
        PositiveAlertTestCase(
            description="Positive test with default events and default alert expected - different sources",
            events=events1 + events2,
            expected_alert=default_alert_aggregated,
        )
    )
