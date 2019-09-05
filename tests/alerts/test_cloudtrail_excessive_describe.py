# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# Copyright (c) 2017 Mozilla Corporation
from .positive_alert_test_case import PositiveAlertTestCase
from .negative_alert_test_case import NegativeAlertTestCase

from .alert_test_suite import AlertTestSuite


class TestCloudtrailExcessiveDescribe(AlertTestSuite):
    alert_filename = "cloudtrail_excessive_describe"
    alert_classname = "AlertCloudtrailExcessiveDescribe"
    num_samples = 2

    default_event = {
        "_source": {
            "category": "AwsApiCall",
            "source": "cloudtrail",
            "details": {
                "eventverb": "Describe",
                "sourceipv4address": "1.2.3.4",
            }
        }
    }

    # This alert is the expected result from running this task
    default_alert = {
        "category": "access",
        "tags": ['cloudtrail'],
        "severity": "WARNING",
        "summary": 'A production service is generating excessive describe calls.',
    }

    test_cases = []

    test_cases.append(
        PositiveAlertTestCase(
            description="Positive test with default events and default alert expected",
            events=AlertTestSuite.create_events(default_event, 5),
            expected_alert=default_alert
        )
    )

    events = AlertTestSuite.create_events(default_event, 5)
    for event in events:
        event['_source']['source'] = 'bad'
    test_cases.append(
        NegativeAlertTestCase(
            description="Negative test case with events with incorrect source",
            events=events,
        )
    )

    events = AlertTestSuite.create_events(default_event, 5)
    for event in events:
        event['_source']['details']['eventverb'] = 'bad'
    test_cases.append(
        NegativeAlertTestCase(
            description="Negative test case with events with incorrect details.eventverb",
            events=events,
        )
    )

    events = AlertTestSuite.create_events(default_event, 5)
    for event in events:
        event['_source']['details']['sourceipv4address'] = None
    test_cases.append(
        NegativeAlertTestCase(
            description="Negative test case with events with non-existent details.sourceipv4address",
            events=events,
        )
    )

    events = AlertTestSuite.create_events(default_event, 5)
    for event in events:
        event['_source']['utctimestamp'] = AlertTestSuite.subtract_from_timestamp_lambda(date_timedelta={'minutes': 6})
        event['_source']['receivedtimestamp'] = AlertTestSuite.subtract_from_timestamp_lambda(date_timedelta={'minutes': 6})
    test_cases.append(
        NegativeAlertTestCase(
            description="Negative test case with old timestamp",
            events=events,
        )
    )
