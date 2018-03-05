# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
# Copyright (c) 2017 Mozilla Corporation

from positive_alert_test_case import PositiveAlertTestCase
from negative_alert_test_case import NegativeAlertTestCase

from alert_test_suite import AlertTestSuite


class TestAlertOpenPortViolation(AlertTestSuite):
    alert_filename = "open_port_violation"

    # This event is the default positive event that will cause the
    # alert to trigger
    default_event = {
        "_type": "event",
        "_source": {
            "category": "open_port_policy_violation",
            "tags": ["open_port_policy_violation"],
            "details": {
                "destinationipaddress": "1.2.3.4",
                "destinationport": 25,
            }
        }
    }

    # This alert is the expected result from running this task
    default_alert = {
        "category": "open_port_policy_violation",
        "tags": ['open_port_policy_violation', 'openportpagerduty'],
        "severity": "CRITICAL",
        "summary": '10 unauthorized open port(s) on 1.2.3.4 (25 25 25 25 25 )',
    }

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
        event['_source']['utctimestamp'] = AlertTestSuite.subtract_from_timestamp_lambda(date_timedelta={'minutes': 239})
        event['_source']['receivedtimestamp'] = AlertTestSuite.subtract_from_timestamp_lambda(date_timedelta={'minutes': 239})
    test_cases.append(
        PositiveAlertTestCase(
            description="Positive test with events a minute earlier",
            events=events,
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
        event['_source']['tags'] = 'bad tag example'
    test_cases.append(
        NegativeAlertTestCase(
            description="Negative test case with events with incorrect tags",
            events=events,
        )
    )

    events = AlertTestSuite.create_events(default_event, 10)
    for event in events:
        event['_source']['utctimestamp'] = AlertTestSuite.subtract_from_timestamp_lambda({'minutes': 241})
        event['_source']['receivedtimestamp'] = AlertTestSuite.subtract_from_timestamp_lambda({'minutes': 241})
    test_cases.append(
        NegativeAlertTestCase(
            description="Negative test case with old timestamp",
            events=events,
        )
    )
