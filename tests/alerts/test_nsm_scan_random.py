# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# Copyright (c) 2017 Mozilla Corporation

from .positive_alert_test_case import PositiveAlertTestCase
from .negative_alert_test_case import NegativeAlertTestCase

from .alert_test_suite import AlertTestSuite


class TestNSMScanRandom(AlertTestSuite):
    alert_filename = "nsm_scan_random"

    # This event is the default positive event that will cause the
    # alert to trigger
    default_event = {
        "_source": {
            "category": "bro",
            "summary": "Scan::Random_Scan source 10.252.25.90 destination unknown port unknown",
            "hostname": "your.friendly.nsm.sensor",
            "tags": ["bro"],
            "source": "notice",
            "details": {
                "sourceipaddress": "10.99.88.77",
                "indicators": "10.99.88.77",
                "source": "notice",
                "note": "Scan::Random_Scan",
            }
        }
    }

    # This alert is the expected result from running this task
    default_alert = {
        "category": "nsm",
        "severity": "WARNING",
        "summary": "Random scan from 10.99.88.77",
        "tags": ['nsm', 'bro', 'randomscan'],
        "notify_mozdefbot": True,
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
            description="Negative test case with a different details.source",
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
        event['_source']['details']['indicators'] = '1.2.3.4'
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
        event['_source']['utctimestamp'] = AlertTestSuite.subtract_from_timestamp_lambda({'minutes': 15})
        event['_source']['receivedtimestamp'] = AlertTestSuite.subtract_from_timestamp_lambda({'minutes': 15})
    test_cases.append(
        NegativeAlertTestCase(
            description="Negative test case with old timestamp",
            events=events,
        )
    )
