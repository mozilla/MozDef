# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# Copyright (c) 2017 Mozilla Corporation

from .positive_alert_test_case import PositiveAlertTestCase
from .negative_alert_test_case import NegativeAlertTestCase

from .alert_test_suite import AlertTestSuite


class TestWriteAudit(AlertTestSuite):
    alert_filename = "write_audit"
    alert_classname = 'WriteAudit'

    # This event is the default positive event that will cause the
    # alert to trigger
    default_event = {
        "_source": {
            "category": "write",
            "summary": "Write: /etc/audit/plugins.d/temp-file.conf",
            "hostname": "exhostname",
            "tags": [
                "audisp-json",
                "2.1.0",
                "audit"
            ],
            "details": {
                "processname": "vi",
                "originaluser": "randomjoe",
                "user": "root",
                "auditkey": "audit",
            }
        }
    }

    # This alert is the expected result from running this task
    default_alert = {
        "category": "write",
        "severity": "WARNING",
        "summary": "5 Filesystem write(s) to an auditd path (/etc/audit/plugins.d/temp-file.conf) by root (randomjoe)",
        "tags": ['audit'],
    }

    test_cases = []

    test_cases.append(
        PositiveAlertTestCase(
            description="Positive test with default event and default alert expected",
            events=AlertTestSuite.create_events(default_event, 5),
            expected_alert=default_alert
        )
    )

    events = AlertTestSuite.create_events(default_event, 5)
    for event in events:
        event['_source']['details']['originaluser'] = 'user1'
    expected_alert = AlertTestSuite.create_alert(default_alert)
    expected_alert['severity'] = 'NOTICE'
    expected_alert['summary'] = "5 Filesystem write(s) to an auditd path (/etc/audit/plugins.d/temp-file.conf) by root (user1)"
    test_cases.append(
        PositiveAlertTestCase(
            description="Positive test with expected downgraded severity",
            events=events,
            expected_alert=expected_alert
        )
    )

    events = AlertTestSuite.create_events(default_event, 5)
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

    events = AlertTestSuite.create_events(default_event, 5)
    for event in events:
        event['_source']['details']['auditkey'] = 'exec'
    test_cases.append(
        NegativeAlertTestCase(
            description="Negative test case with events with auditkey without 'audit'",
            events=events,
        )
    )

    events = AlertTestSuite.create_events(default_event, 5)
    for event in events:
        event['_source']['details']['processname'] = 'process1'
    test_cases.append(
        NegativeAlertTestCase(
            description="Negative test case with events with processname that matches exclusion of 'process1'",
            events=events,
        )
    )

    events = AlertTestSuite.create_events(default_event, 5)
    for event in events:
        event['_source']['details']['originaluser'] = None
    test_cases.append(
        NegativeAlertTestCase(
            description="Negative test case aggregation key excluded",
            events=events,
        )
    )

    events = AlertTestSuite.create_events(default_event, 5)
    for event in events:
        event['_source']['utctimestamp'] = AlertTestSuite.subtract_from_timestamp_lambda({'minutes': 20})
        event['_source']['receivedtimestamp'] = AlertTestSuite.subtract_from_timestamp_lambda({'minutes': 20})
    test_cases.append(
        NegativeAlertTestCase(
            description="Negative test case with old timestamp",
            events=events,
        )
    )
