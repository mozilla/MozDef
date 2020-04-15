# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# Copyright (c) 2017 Mozilla Corporation
from .positive_alert_test_case import PositiveAlertTestCase
from .negative_alert_test_case import NegativeAlertTestCase

from .alert_test_suite import AlertTestSuite


class TestDeadmanGeneric(AlertTestSuite):
    alert_filename = "deadman_generic"
    alert_classname = "AlertDeadmanGeneric"
    deadman = True

    default_event = {
        "_source": {
            "category": "helloworld",
            "details": {
                "sourceipaddress": "1.2.3.4",
            }
        }
    }

    test_cases = []

    matched_event_second = {
        "_source": {
            "summary": "anotherterm",
        }
    }
    unmatched_first_alert = {
        "category": "deadman",
        "tags": ['deadman', 'generic_deadman'],
        "severity": "ERROR",
        "summary": 'Deadman check failed for \'Sample Alert 1\' the past 5 minutes',
    }
    test_cases.append(
        PositiveAlertTestCase(
            description="Positive test that causes first alert configuration to throw",
            events=[AlertTestSuite.create_event(matched_event_second)],
            expected_alert=unmatched_first_alert
        )
    )

    matched_event_first = {
        "_source": {
            "summary": "ABC12345436",
        }
    }
    unmatched_second_alert = {
        "category": "deadman",
        "tags": ['deadman', 'someothertag'],
        "severity": "ERROR",
        "summary": 'Deadman check failed for \'Sample Alert 2\' the past 20 hours',
    }
    test_cases.append(
        PositiveAlertTestCase(
            description="Positive test that causes second alert configuration to throw",
            events=[AlertTestSuite.create_event(matched_event_first)],
            expected_alert=unmatched_second_alert
        )
    )

    test_cases.append(
        NegativeAlertTestCase(
            description="Negative test case with events with incorrect category",
            events=[AlertTestSuite.create_event(matched_event_first), AlertTestSuite.create_event(matched_event_second)]
        )
    )

    events = [
        AlertTestSuite.create_event(matched_event_first),
        AlertTestSuite.create_event(matched_event_second)
    ]
    events[0]['_source']['utctimestamp'] = AlertTestSuite.subtract_from_timestamp_lambda(date_timedelta={'minutes': 6})
    events[0]['_source']['receivedtimestamp'] = AlertTestSuite.subtract_from_timestamp_lambda(date_timedelta={'minutes': 6})
    test_cases.append(
        PositiveAlertTestCase(
            description="Positive test case with events matching first alert configuration but are old",
            events=events,
            expected_alert=unmatched_first_alert
        )
    )

    events = [
        AlertTestSuite.create_event(matched_event_first),
        AlertTestSuite.create_event(matched_event_second)
    ]
    events[1]['_source']['utctimestamp'] = AlertTestSuite.subtract_from_timestamp_lambda(date_timedelta={'hours': 21})
    events[1]['_source']['receivedtimestamp'] = AlertTestSuite.subtract_from_timestamp_lambda(date_timedelta={'hours': 21})
    test_cases.append(
        PositiveAlertTestCase(
            description="Positive test case with events matching second alert configuration but are old",
            events=events,
            expected_alert=unmatched_second_alert
        )
    )
