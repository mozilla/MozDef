# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# Copyright (c) 2017 Mozilla Corporation

from .positive_alert_test_case import PositiveAlertTestCase
from .negative_alert_test_case import NegativeAlertTestCase

from .alert_test_suite import AlertTestSuite


class TestTraceAudit(AlertTestSuite):
    alert_filename = "trace_audit"
    alert_classname = 'TraceAudit'

    # This event is the default positive event that will cause the
    # alert to trigger
    default_event = {
        "_source": {
            "category": "ptrace",
            "summary": "Ptrace",
            "hostname": "exhostname",
            "tags": ["audisp-json","2.1.0", "audit"],
            "details": {
                "processname": "strace",
                "originaluser": "randomjoe",
                "auditkey": "strace",
            }
        }
    }

    # This alert is the expected result from running this task
    default_alert = {
        "category": "trace",
        "severity": "WARNING",
        "summary": "5 instances of Strace or Ptrace executed by randomjoe on exhostname",
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
        event['_source']['summary'] = 'Unknown'
    test_cases.append(
        PositiveAlertTestCase(
            description="Positive test with events with a summary of 'Write: /etc/audit/rules.d/'",
            events=events,
            expected_alert=default_alert
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
        event['_source']['hostname'] = 'example.hostname.com'
    test_cases.append(
        NegativeAlertTestCase(
            description="Negative test case with events with example hostname that matches exclusion of 'hostfilter'",
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
        event['_source']['utctimestamp'] = AlertTestSuite.subtract_from_timestamp_lambda({'minutes': 15})
        event['_source']['receivedtimestamp'] = AlertTestSuite.subtract_from_timestamp_lambda({'minutes': 15})
    test_cases.append(
        NegativeAlertTestCase(
            description="Negative test case with old timestamp",
            events=events,
        )
    )
