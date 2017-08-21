#!/usr/bin/env python
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
# Copyright (c) 2017 Mozilla Corporation
#
# Contributors:
# Michal Purzynski mpurzynski@mozilla.com

from positive_alert_test_case import PositiveAlertTestCase
from negative_alert_test_case import NegativeAlertTestCase

from alert_test_suite import AlertTestSuite

from datetime import datetime


class TestSessionOpenedUser(AlertTestSuite):
    alert_filename = "session_opened_sensitive_user"

    # This event is the default positive event that will cause the
    # alert to trigger
    default_event = {
        "_type": "event",
        "_source": {
            "category": "syslog",
            "summary": 'pam_unix(sshd:session): session opened for user user1 by (uid=0)',
            "details": {
                "program": "sshd",
                "hostname": "exhostname",
            }
        }
    }

    # This alert is the expected result from running this task
    default_alert = {
        "category": "session",
        "severity": "WARNING",
        "tags": ['pam', 'syslog'],
        "summary": "sshd session opened for scanning user outside of the expected window on exhostname [10]"
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
        event['_source']['utctimestamp'] = AlertTestSuite.create_timestamp_from_now_lambda(hour=5, minute=55, second=30)
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
       event['_type'] = 'badtype'
    test_cases.append(
       NegativeAlertTestCase(
           description="Negative test case with events with wrong type",
           events=events,
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
       event['_source']['utctimestamp'] = AlertTestSuite.subtract_from_timestamp_lambda({'minutes': 5})
    test_cases.append(
       NegativeAlertTestCase(
           description="Negative test case with old timestamp",
           events=events,
       )
    )