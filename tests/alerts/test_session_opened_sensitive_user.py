#!/usr/bin/env python
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# Copyright (c) 2017 Mozilla Corporation

from .positive_alert_test_case import PositiveAlertTestCase
from .negative_alert_test_case import NegativeAlertTestCase

from .alert_test_suite import AlertTestSuite


class TestSessionOpenedUser(AlertTestSuite):
    alert_filename = "session_opened_sensitive_user"

    # This event is the default positive event that will cause the
    # alert to trigger
    default_event = {
        "_source": {
            "category": "syslog",
            "hostname": "exhostname",
            "summary": 'pam_unix(sshd:session): session opened for user user1 by (uid=0)',
            "details": {
                "program": "sshd",
            }
        }
    }

    # This alert is the expected result from running this task
    default_alert = {
        "category": "session",
        "severity": "WARNING",
        "tags": ['pam', 'syslog'],
        "summary": "Session opened by a sensitive user outside of the expected window - sample hosts: exhostname [total 10 hosts]"
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
        event['_source']['summary'] = 'pam_unix(sshd:session): session opened for user user2 by (uid=0)'
    test_cases.append(
        PositiveAlertTestCase(
            description="Positive test with events with a user 'user2'",
            events=events,
            expected_alert=default_alert
        )
    )

    events = AlertTestSuite.create_events(default_event, 10)
    for event in events:
        event['_source']['summary'] = 'pam_unix(sshd:session): session opened for user user1 by (uid=0)'
    test_cases.append(
        PositiveAlertTestCase(
            description="Positive test with events with a user 'user1'",
            events=events,
            expected_alert=default_alert
        )
    )

    events = AlertTestSuite.create_events(default_event, 10)
    randomhostsalert = AlertTestSuite.copy(default_alert)
    randomhostsalert['summary'] = "Session opened by a sensitive user outside of the expected window - sample hosts:"
    for event in events:
        randomhostname = 'host' + str(events.index(event))
        event['_source']['hostname'] = randomhostname
        randomhostsalert['summary'] += ' {0}'.format(randomhostname)
    randomhostsalert['summary'] += " [total 10 hosts]"
    test_cases.append(
        PositiveAlertTestCase(
            description="Positive test with events with a user 'user1'",
            events=events,
            expected_alert=randomhostsalert
        )
    )

    events = AlertTestSuite.create_events(default_event, 10)
    for event in events:
        event['_source']['summary'] = 'pam_unix(sshd:session): session opened for user user3 by (uid=0)'
    test_cases.append(
        NegativeAlertTestCase(
            description="Negative test with wrong username",
            events=events
        )
    )

    events = AlertTestSuite.create_events(default_event, 10)
    for event in events:
        event['_source']['utctimestamp'] = AlertTestSuite.create_timestamp_from_now_lambda(hour=3, minute=45, second=30)
        event['_source']['receivedtimestamp'] = AlertTestSuite.create_timestamp_from_now_lambda(hour=3, minute=45, second=30)
    test_cases.append(
        NegativeAlertTestCase(
            description="Negative test with events inside whitelisted time",
            events=events,
        )
    )

    events = AlertTestSuite.create_events(default_event, 10)
    for event in events:
        event['_source']['summary'] = 'login failed'
    test_cases.append(
        NegativeAlertTestCase(
            description="Negative test with events with a summary of 'login failed'",
            events=events
        )
    )

    events = AlertTestSuite.create_events(default_event, 10)
    for event in events:
        event['_source']['category'] = 'badcategory'
    test_cases.append(
        NegativeAlertTestCase(
            description="Negative test case with events with wrong category",
            events=events,
        )
    )

    events = AlertTestSuite.create_events(default_event, 10)
    for event in events:
        event['_source']['details']['program'] = 'ssh'
    test_cases.append(
        NegativeAlertTestCase(
            description="Negative test case with events with wrong program",
            events=events,
        )
    )

    events = AlertTestSuite.create_events(default_event, 10)
    for event in events:
        event['_source']['summary'] = 'pam_unix(sshd:session): session closed for user user1 by (uid=0)'
    test_cases.append(
        NegativeAlertTestCase(
            description="Negative test case with events with 'session closed' summary",
            events=events,
        )
    )

    events = AlertTestSuite.create_events(default_event, 10)
    for event in events:
        event['_source']['utctimestamp'] = AlertTestSuite.subtract_from_timestamp_lambda({'minutes': 15})
        event['_source']['receivedtimestamp'] = AlertTestSuite.subtract_from_timestamp_lambda({'minutes': 15})
    test_cases.append(
        NegativeAlertTestCase(
            description="Negative test case with old timestamp",
            events=events,
        )
    )
