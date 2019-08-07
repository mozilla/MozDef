# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# Copyright (c) 2017 Mozilla Corporation

from .positive_alert_test_case import PositiveAlertTestCase
from .negative_alert_test_case import NegativeAlertTestCase

from .alert_test_suite import AlertTestSuite


class TestAlertBruteforceSsh(AlertTestSuite):
    alert_filename = "bruteforce_ssh"

    # This event is the default positive event that will cause the
    # alert to trigger
    default_event = {
        "_source": {
            "summary": 'login invalid ldap_count_entries failed by 1.2.3.4',
            "hostname": "exhostname",
            "details": {
                "program": "sshd",
                "sourceipaddress": "1.2.3.4",
            }
        }
    }

    # This alert is the expected result from running this task
    default_alert = {
        "category": "bruteforce",
        "severity": "NOTICE",
        "summary": "10 ssh bruteforce attempts by 1.2.3.4 exhostname (10 hits)",
        "tags": ['ssh'],
    }

    test_cases = []

    test_cases.append(
        PositiveAlertTestCase(
            description="Positive test with default event and default alert expected",
            events=AlertTestSuite.create_events(default_event, 10),
            expected_alert=default_alert
        )
    )

    events = AlertTestSuite.create_events(default_event, 10)
    for event in events:
        event['_source']['utctimestamp'] = AlertTestSuite.subtract_from_timestamp_lambda(date_timedelta={'minutes': 1})
        event['_source']['receivedtimestamp'] = AlertTestSuite.subtract_from_timestamp_lambda(date_timedelta={'minutes': 1})
    test_cases.append(
        PositiveAlertTestCase(
            description="Positive test with events a minute earlier",
            events=events,
            expected_alert=default_alert
        )
    )

    events = AlertTestSuite.create_events(default_event, 10)
    for event in events:
        event['_source']['summary'] = 'login failed'
    test_cases.append(
        PositiveAlertTestCase(
            description="Positive test with events with a summary of 'login failed'",
            events=events,
            expected_alert=default_alert
        )
    )

    events = AlertTestSuite.create_events(default_event, 10)
    for event in events:
        event['_source']['summary'] = 'invalid failed'
    test_cases.append(
        PositiveAlertTestCase(
            description="Positive test with events with a summary of 'invalid failed'",
            events=events,
            expected_alert=default_alert
        )
    )

    events = AlertTestSuite.create_events(default_event, 10)
    for event in events:
        event['_source']['summary'] = 'invalid failed'
    test_cases.append(
        PositiveAlertTestCase(
            description="Positive test with events with a summary of 'ldap_count_entries failed'",
            events=events,
            expected_alert=default_alert
        )
    )

    events = AlertTestSuite.create_events(default_event, 10)
    events[8]['_source']['details']['sourceipaddress'] = "127.0.0.1"
    events[9]['_source']['details']['sourceipaddress'] = "127.0.0.1"
    test_cases.append(
        NegativeAlertTestCase(
            description="Negative test case with 10 events however one has different sourceipaddress",
            events=events,
        )
    )

    test_cases.append(
        NegativeAlertTestCase(
            description="Negative test case with not enough events",
            events=AlertTestSuite.create_events(default_event, 9),
        ),
    )

    events = AlertTestSuite.create_events(default_event, 10)
    for event in events:
        event['_source']['summary'] = 'login good ldap_count_entries'
    test_cases.append(
        NegativeAlertTestCase(
            description="Negative test case with events with summary without 'failed'",
            events=events,
        )
    )

    events = AlertTestSuite.create_events(default_event, 10)
    for event in events:
        event['_source']['summary'] = 'failed'
    test_cases.append(
        NegativeAlertTestCase(
            description="Negative test case with events with summary with only 'failed'",
            events=events,
        )
    )

    events = AlertTestSuite.create_events(default_event, 10)
    for event in events:
        event['_source']['summary'] = 'login'
    test_cases.append(
        NegativeAlertTestCase(
            description="Negative test case with events with summary with only 'login'",
            events=events,
        )
    )

    events = AlertTestSuite.create_events(default_event, 10)
    for event in events:
        event['_source']['summary'] = 'invalid'
    test_cases.append(
        NegativeAlertTestCase(
            description="Negative test case with events with summary with only 'invalid'",
            events=events,
        )
    )

    events = AlertTestSuite.create_events(default_event, 10)
    for event in events:
        event['_source']['summary'] = 'ldap_count_entries'
    test_cases.append(
        NegativeAlertTestCase(
            description="Negative test case with events with summary with only 'ldap_count_entries'",
            events=events,
        )
    )

    events = AlertTestSuite.create_events(default_event, 10)
    for event in events:
        event['_source']['details']['program'] = 'badprogram'
    test_cases.append(
        NegativeAlertTestCase(
            description="Negative test case with events with bad program",
            events=events,
        )
    )

    events = AlertTestSuite.create_events(default_event, 10)
    for event in events:
        event['_source']['utctimestamp'] = AlertTestSuite.subtract_from_timestamp_lambda({'minutes': 3})
        event['_source']['receivedtimestamp'] = AlertTestSuite.subtract_from_timestamp_lambda({'minutes': 3})
    test_cases.append(
        NegativeAlertTestCase(
            description="Negative test case with old timestamp",
            events=events,
        )
    )

    events = AlertTestSuite.create_events(default_event, 10)
    for event in events:
        event['_source']['summary'] = event['_source']['summary'].replace('1.2.3.4', '11.22.33.44')
    test_cases.append(
        NegativeAlertTestCase(
            description="Negative test case with 11.22.33.44 as a whitelisted ip",
            events=events,
        )
    )

    events = AlertTestSuite.create_events(default_event, 10)
    for event in events:
        event['_source']['summary'] = event['_source']['summary'].replace('1.2.3.4', '55.66.77.88')
    test_cases.append(
        NegativeAlertTestCase(
            description="Negative test case with 55.66.77.88 as a whitelisted ip",
            events=events,
        )
    )

    events = AlertTestSuite.create_events(default_event, 10)
    for event in events:
        event['_source']['details']['sourceipaddress'] = None
    test_cases.append(
        NegativeAlertTestCase(
            description="Negative test case aggregation key excluded",
            events=events,
        )
    )
