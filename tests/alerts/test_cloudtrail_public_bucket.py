# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# Copyright (c) 2017 Mozilla Corporation
from .positive_alert_test_case import PositiveAlertTestCase
from .negative_alert_test_case import NegativeAlertTestCase

from .alert_test_suite import AlertTestSuite


class TestCloudtrailPublicBucket(AlertTestSuite):
    alert_filename = "cloudtrail_public_bucket"
    alert_classname = "AlertCloudtrailPublicBucket"

    default_event = {
        "_source": {
            "source": "cloudtrail",
            "details": {
                "requestparameters": {
                    "x-amz-acl": "public-read-write",
                    "bucketname": "testbucket"
                },
                "eventname": "CreateBucket",
            },
        }
    }

    # This alert is the expected result from running this task
    default_alert = {
        "category": "access",
        "tags": ['cloudtrail'],
        "severity": "INFO",
        "summary": 'The s3 bucket testbucket is listed as public',
    }

    test_cases = []

    test_cases.append(
        PositiveAlertTestCase(
            description="Positive test with default events and default alert expected",
            events=[AlertTestSuite.create_event(default_event)],
            expected_alert=default_alert
        )
    )

    event = AlertTestSuite.create_event(default_event)
    event['_source']['source'] = 'bad'
    test_cases.append(
        NegativeAlertTestCase(
            description="Negative test case with events with incorrect source",
            events=[event],
        )
    )

    event = AlertTestSuite.create_event(default_event)
    event['_source']['details']['eventname'] = 'bad'
    test_cases.append(
        NegativeAlertTestCase(
            description="Negative test case with events with incorrect details.eventname",
            events=[event],
        )
    )

    event = AlertTestSuite.create_event(default_event)
    event['_source']['details']['requestparameters']['x-amz-acl'] = 'test'
    test_cases.append(
        NegativeAlertTestCase(
            description="Negative test case with events with incorrect field",
            events=[event],
        )
    )

    event = AlertTestSuite.create_event(default_event)
    event['_source']['utctimestamp'] = AlertTestSuite.subtract_from_timestamp_lambda(date_timedelta={'minutes': 21})
    event['_source']['receivedtimestamp'] = AlertTestSuite.subtract_from_timestamp_lambda(date_timedelta={'minutes': 21})
    test_cases.append(
        NegativeAlertTestCase(
            description="Negative test case with old timestamp",
            events=[event],
        )
    )
