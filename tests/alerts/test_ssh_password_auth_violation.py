# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# Copyright (c) 2017 Mozilla Corporation

from .positive_alert_test_case import PositiveAlertTestCase
from .negative_alert_test_case import NegativeAlertTestCase

from .alert_test_suite import AlertTestSuite


class TestAlertSSHPasswordAuthViolation(AlertTestSuite):
    alert_filename = "ssh_password_auth_violation"

    # This event is the default positive event that will cause the
    # alert to trigger
    default_event = {
        "_source": {
            "category": "ssh_password_auth_policy_violation",
            "tags": ["ssh_password_auth_policy_violation"],
            "details": {
                "destinationipaddress": "1.2.3.4",
                "destinationport": 22,
            }
        }
    }

    # This alert is the expected result from running this task
    default_alert = {
        "category": "ssh_password_auth_policy_violation",
        "tags": ['ssh_password_auth_policy_violation'],
        "severity": "WARNING",
        "summary": 'SSH password authentication allowed on 1.2.3.4',
    }

    test_cases = []

    test_cases.append(
        PositiveAlertTestCase(
            description="Positive test with default events and default alert expected",
            events=AlertTestSuite.create_events(default_event, 1),
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
