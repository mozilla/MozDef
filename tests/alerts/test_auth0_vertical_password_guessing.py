# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# Copyright (c) 2017 Mozilla Corporation

from .positive_alert_test_case import PositiveAlertTestCase
from .negative_alert_test_case import NegativeAlertTestCase

from .alert_test_suite import AlertTestSuite


class TestAuth0VerticalPasswordGuessing(AlertTestSuite):
    alert_filename = "auth0_vertical_password_guessing"
    alert_classname = "AlertAuth0VerticalPasswordGuessing"

    # This event is the default positive event that will cause the
    # alert to trigger
    default_event = {
        "_source": {
            "details": {
                "connection": "Mozilla-LDAP",
                "description": "Wrong email or password.",
                "eventname": "Failed Login (wrong password)",
                "sourceipaddress": "1.1.1.1",
                "success": False,
                "useragent": "Firefox 80.0.0 / Windows 10.0.0",
                "userid": "ad|foo",
                "username": "foo@mozilla.com",
            },
            "category": "authentication",
            "severity": "ERROR",
            "summary": "Failed Login (wrong password) Wrong email or password. by foo@mozilla.com",
            "tags": [
                "auth0"
            ],
            "type": "event",
        }
    }

    default_event2 = AlertTestSuite.copy(default_event)
    default_event2["_source"]["details"]["sourceipaddress"] = "1.1.1.2"
    default_event2["_source"]["details"]["username"] = "bar"

    # This alert is the expected result from running this task
    default_alert = {
        "category": "bruteforce",
        "tags": ["auth0"],
        "severity": "WARNING",
        "summary": "Auth0 Username/Password Vertical Password Guessing Attack in Progress against 2 users from 2 unique source ip(s)",
    }

    # This alert is the expected result from this task against multiple matching events
    default_alert_aggregated = AlertTestSuite.copy(default_alert)
    default_alert_aggregated[
        "summary"
    ] = "Auth0 Username/Password Vertical Password Guessing Attack in Progress against 2 users from 2 unique source ip(s)"

    test_cases = []

    test_cases.append(
        PositiveAlertTestCase(
            description="Positive test with default events and default alert expected",
            events=AlertTestSuite.create_events(default_event, 5) + AlertTestSuite.create_events(default_event2, 5),
            expected_alert=default_alert,
        )
    )

    test_cases.append(
        NegativeAlertTestCase(
            description="Negative test with only one affected user",
            events=AlertTestSuite.create_events(default_event, 5)
        )
    )

    test_cases.append(
        PositiveAlertTestCase(
            description="Positive test with default events and default alert expected - dedup",
            events=AlertTestSuite.create_events(default_event, 5) + AlertTestSuite.create_events(default_event2, 5),
            expected_alert=default_alert,
        )
    )

    events = AlertTestSuite.create_events(default_event, 5) + AlertTestSuite.create_events(default_event2, 5)
    for event in events:
        event["_source"]["details"]["eventname"] = "Success Login"
    test_cases.append(
        NegativeAlertTestCase(
            description="Negative test with default negative event", events=events
        )
    )

    events = AlertTestSuite.create_events(default_event, 5) + AlertTestSuite.create_events(default_event2, 5)
    for event in events:
        event["_source"]["tags"] = ["bad"]
    test_cases.append(
        NegativeAlertTestCase(
            description="Negative test case with events with incorrect tags",
            events=events,
        )
    )

    events = AlertTestSuite.create_events(default_event, 5) + AlertTestSuite.create_events(default_event2, 5)
    for event in events:
        event["_source"][
            "utctimestamp"
        ] = AlertTestSuite.subtract_from_timestamp_lambda({"minutes": 241})
        event["_source"][
            "receivedtimestamp"
        ] = AlertTestSuite.subtract_from_timestamp_lambda({"minutes": 241})
    test_cases.append(
        NegativeAlertTestCase(
            description="Negative test case with old timestamp", events=events
        )
    )
