# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# Copyright (c) 2017 Mozilla Corporation

from .positive_alert_test_case import PositiveAlertTestCase
from .negative_alert_test_case import NegativeAlertTestCase

from .alert_test_suite import AlertTestSuite


class TestAlertProxyDropNonStandardPort(AlertTestSuite):
    alert_filename = "proxy_drop_non_standard_port"

    # This event is the default positive event that will cause the
    # alert to trigger
    default_event = {
        "_source": {
            "category": "proxy",
            "details": {
                "sourceipaddress": "1.2.3.4",
                "destination": "evil.com:1337",
                "destinationport": "1337",
                "proxyaction": "TCP_DENIED",
                "method": "CONNECT",
            },
        },
    }

    default_event2 = AlertTestSuite.copy(default_event)
    default_event2["_source"]["details"]["destination"] = "evil.com:6667"
    default_event2["_source"]["details"]["destinationport"] = "6667"

    # This alert is the expected result from running this task
    default_alert = {
        "category": "squid",
        "tags": ["squid", "proxy"],
        "severity": "WARNING",
        "summary": "Suspicious Proxy DROP event(s) detected from 1.2.3.4 to the following non-std port destination(s): evil.com:1337",
    }

    default_alert_aggregated = AlertTestSuite.copy(default_alert)
    default_alert_aggregated[
        "summary"
    ] = "Suspicious Proxy DROP event(s) detected from 1.2.3.4 to the following non-std port destination(s): evil.com:1337,evil.com:6667"

    test_cases = []

    test_cases.append(
        PositiveAlertTestCase(
            description="Positive test with default events and default alert expected",
            events=AlertTestSuite.create_events(default_event, 1),
            expected_alert=default_alert,
        )
    )

    events1 = AlertTestSuite.create_events(default_event, 1)
    events2 = AlertTestSuite.create_events(default_event2, 1)
    test_cases.append(
        PositiveAlertTestCase(
            description="Positive test with default events and default alert expected",
            events=events1 + events2,
            expected_alert=default_alert_aggregated,
        )
    )

    events = AlertTestSuite.create_events(default_event, 10)
    for event in events:
        event["_source"]["details"]["destinationport"] = "443"
    test_cases.append(
        NegativeAlertTestCase(
            description="Negative test case with events with whitelisted port",
            events=events,
        )
    )

    events = AlertTestSuite.create_events(default_event, 10)
    for event in events:
        event["_source"]["category"] = "bad"
    test_cases.append(
        NegativeAlertTestCase(
            description="Negative test case with events with incorrect category",
            events=events,
        )
    )

    events = AlertTestSuite.create_events(default_event, 10)
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
