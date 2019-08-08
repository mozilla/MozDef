# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# Copyright (c) 2017 Mozilla Corporation

from .positive_alert_test_case import PositiveAlertTestCase
from .negative_alert_test_case import NegativeAlertTestCase

from .alert_test_suite import AlertTestSuite


class TestNSMScanPort(AlertTestSuite):
    alert_filename = "nsm_scan_port"

    # This event is the default positive event that will cause the
    # alert to trigger
    default_event = {
        "_source": {
            "category": "bro",
            "summary": "Scan::Port_Scan source 10.99.88.77 destination unknown port unknown",
            "hostname": "your.friendly.nsm.sensor",
            "tags": ["bro"],
            "source": "notice",
            "details": {
                "sourceipaddress": "10.99.88.77",
                "indicators": "10.99.88.77",
                "note": "Scan::Port_Scan",
            }
        }
    }

    # This alert is the expected result from running this task
    default_alert = {
        "category": "nsm",
        "severity": "WARNING",
        "summary": "Port scan from 10.99.88.77 (mock.mozilla.org)",
        "tags": ['nsm', 'bro', 'portscan'],
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
        event['_source']['category'] = 'syslog'
    test_cases.append(
        NegativeAlertTestCase(
            description="Negative test case with a different category",
            events=events,
        )
    )

    events = AlertTestSuite.create_events(default_event, 5)
    for event in events:
        event['_source']['source'] = 'intel'
    test_cases.append(
        NegativeAlertTestCase(
            description="Negative test case with a different source",
            events=events,
        )
    )

    events = AlertTestSuite.create_events(default_event, 5)
    for event in events:
        event['_source']['details']['note'] = 'Scan::Address_Scan'
    test_cases.append(
        NegativeAlertTestCase(
            description="Negative test case with a different scan type (note)",
            events=events,
        )
    )

    events = AlertTestSuite.create_events(default_event, 5)
    for event in events:
        event['_source']['details']['sourceipaddress'] = '10.54.65.234'
        event['_source']['details']['indicators'] = '10.54.65.234'
    test_cases.append(
        NegativeAlertTestCase(
            description="Negative test case with an excluded IP address",
            events=events,
        )
    )

    events = AlertTestSuite.create_events(default_event, 5)
    for event in events:
        event['_source']['details']['sourceipaddress'] = '1.2.3.4'
        event['_source']['details']['indicators'] = '1.2.3.4'
    test_cases.append(
        NegativeAlertTestCase(
            description="Negative test case with an excluded subnet",
            events=events,
        )
    )

    events = AlertTestSuite.create_events(default_event, 5)
    for event in events:
        event['_source']['details']['sourceipaddress'] = '1.2.3.4'
        event['_source']['details']['indicators'] = '1.2.3.4'
        event['_source']['details']['msg'] = '2620:101:80f8:224:44af:81c2:372c:6cbf scanned at least 15 unique ports on hosts 2001:41d0:e:9d4::1, 192.168.1.1, 2400:6180:0:d0::4a6b:4001, 2a03:b0c0:1:e0::13a:2001, 2001:0:3e8a:ee2d:5c:3162:3f57:fd8d in 0m11s'
    test_cases.append(
        NegativeAlertTestCase(
            description="Negative test case with an excluded destination",
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
