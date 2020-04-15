# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# Copyright (c) 2017 Mozilla Corporation
from .positive_alert_test_case import PositiveAlertTestCase
from .negative_alert_test_case import NegativeAlertTestCase

from .alert_test_suite import AlertTestSuite


class TestProxyExfilDomains(AlertTestSuite):
    alert_filename = "proxy_exfil_domains"
    alert_classname = "AlertProxyExfilDomains"

    # This event is the default positive event that will cause the
    # alert to trigger
    default_event = {
        "_source": {
            "category": "proxy",
            "details": {"sourceipaddress": "1.2.3.4", "host": "pastebin.com"},
        },
    }

    # This event is an alternate destination that we'd want to aggregate
    default_event2 = AlertTestSuite.copy(default_event)
    default_event2["_source"]["details"]["host"] = "www.sendspace.com"

    # This event is the default negative event that will not cause the
    # alert to trigger
    default_negative_event = AlertTestSuite.copy(default_event)
    default_negative_event["_source"]["details"]["host"] = "foo.mozilla.com"

    # This alert is the expected result from running this task
    default_alert = {
        "category": "squid",
        "tags": ["squid", "proxy"],
        "severity": "WARNING",
        "summary": "Proxy drop events detected from 1.2.3.4 to the following domain(s) that are known for exfiltrating data: pastebin.com",
    }

    default_alert2 = {
        "category": "squid",
        "tags": ["squid", "proxy"],
        "severity": "WARNING",
        "summary": "Proxy drop events detected from 1.2.3.4 to the following domain(s) that are known for exfiltrating data: www.sendspace.com",
    }

    # This alert is the expected result from this task against multiple matching events
    default_alert_aggregated = AlertTestSuite.copy(default_alert)
    default_alert_aggregated[
        "summary"
    ] = "Proxy drop events detected from 1.2.3.4 to the following domain(s) that are known for exfiltrating data: pastebin.com,www.sendspace.com"

    test_cases = []

    test_cases.append(
        PositiveAlertTestCase(
            description="Positive test with default events and default alert expected",
            events=AlertTestSuite.create_events(default_event, 1),
            expected_alert=default_alert,
        )
    )

    test_cases.append(
        PositiveAlertTestCase(
            description="Positive test with default events and default alert expected - dedup",
            events=AlertTestSuite.create_events(default_event, 2),
            expected_alert=default_alert,
        )
    )

    test_cases.append(
        PositiveAlertTestCase(
            description="Positive test with default events and default alert expected - dedup",
            events=AlertTestSuite.create_events(default_event2, 2),
            expected_alert=default_alert2,
        )
    )

    events1 = AlertTestSuite.create_events(default_event, 1)
    events2 = AlertTestSuite.create_events(default_event2, 1)
    test_cases.append(
        PositiveAlertTestCase(
            description="Positive test with default events and default alert expected - different destinations",
            events=events1 + events2,
            expected_alert=default_alert_aggregated,
        )
    )

    test_cases.append(
        NegativeAlertTestCase(
            description="Negative test with default negative event",
            events=AlertTestSuite.create_events(default_negative_event, 1),
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
