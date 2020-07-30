# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# Copyright (c) 2017 Mozilla Corporation

from .positive_alert_test_case import PositiveAlertTestCase
from .negative_alert_test_case import NegativeAlertTestCase

from .alert_test_suite import AlertTestSuite


class TestAlertTriageBotEscalation(AlertTestSuite):
    alert_filename = "triagebot_escalation"
    alert_classname = 'AlertTriageBotEscalation'

    # This event is the default positive event that will cause the
    # alert to trigger
    default_event = {
        "_source": {
            "hostname": "UNKNOWN",
            "details": {
                "identifier": "UdEkkIEJFXEy54grVnfy",
                "identityConfidence": "low",
                "email": "test@testerson.com",
                "slack": "U4J8Z3DJT",
                "userresponse": "no"
            },
            "category": "triagebot",
            "summary": "TriageBot Response: no from: test@testerson.com"
        }
    }

    # This alert is the expected result from running this task
    default_alert = {
        "category": "access",
        "severity": "INFO",
        "summary": "TriageBot Escalation for event: UdEkkIEJFXEy54grVnfy sent to PagerDuty per 'NO' response from User: test@testerson.com",
        "tags": ['triagebot_escalation'],
    }

    test_cases = []

    test_cases.append(
        PositiveAlertTestCase(
            description="Positive test with default event and default alert expected",
            events=AlertTestSuite.create_events(default_event, 1),
            expected_alert=default_alert
        )
    )

    event = AlertTestSuite.create_event(default_event)
    event['_source']['details']['identifier'] = 'AbDpsIOPERXEy54grVnfy'
    alert = AlertTestSuite.create_alert(default_alert)
    alert['summary'] = "TriageBot Escalation for event: AbDpsIOPERXEy54grVnfy sent to PagerDuty per 'NO' response from User: test@testerson.com"
    test_cases.append(
        PositiveAlertTestCase(
            description="Positive test with different event_id in the summary",
            events=[event],
            expected_alert=alert
        )
    )

    event = AlertTestSuite.create_event(default_event)
    event['_source']['details']['userresponse'] = 'yes'
    test_cases.append(
        NegativeAlertTestCase(
            description="Negative test with events with a user response of 'yes'",
            events=[event],
        )
    )

    event = AlertTestSuite.create_event(default_event)
    event['_source']['details']['email'] = None
    test_cases.append(
        NegativeAlertTestCase(
            description="Negative test case email key excluded",
            events=[event],
        )
    )

    event = AlertTestSuite.create_event(default_event)
    event['_source']['category'] = 'bad'
    test_cases.append(
        NegativeAlertTestCase(
            description="Negative test case with bad category key",
            events=[event],
        )
    )
