from positive_alert_test_case import PositiveAlertTestCase
from negative_alert_test_case import NegativeAlertTestCase

from alert_test_suite import AlertTestSuite


class TestAlertCloudtrailLoggingDisabled(AlertTestSuite):
    alert_filename = "cloudtrail_logging_disabled"

    # This event is the default positive event that will cause the
    # alert to trigger
    default_event = {
        "_type": "cloudtrail",
        "_source": {
            "eventName": "StopLogging",
            "requestParameters": {
                "name": "cloudtrail_example_name"
            }
        }
    }

    # This alert is the expected result from running this task
    default_alert = {
        "category": "AWSCloudtrail",
        "severity": "CRITICAL",
        "summary": "Cloudtrail Logging Disabled: cloudtrail_example_name",
        "tags": ['cloudtrail', 'aws', 'cloudtrailpagerduty'],
    }

    test_cases = []

    event = AlertTestSuite.create_event(default_event)
    test_cases.append(
        PositiveAlertTestCase(
            description="Positive test case with good event",
            events=[event],
            expected_alert=default_alert
        )
    )

    event = AlertTestSuite.create_event(default_event)
    event['_source']['utctimestamp'] = AlertTestSuite.subtract_from_timestamp_lambda({'minutes': 29})
    test_cases.append(
        PositiveAlertTestCase(
            description="Positive test case with an event with somewhat old timestamp",
            events=[event],
            expected_alert=default_alert
        )
    )

    event = AlertTestSuite.create_event(default_event)
    event['_type'] = 'event'
    test_cases.append(
        NegativeAlertTestCase(
            description="Negative test case with bad event type",
            events=[event],
        )
    )

    event = AlertTestSuite.create_event(default_event)
    event['_source']['eventName'] = 'Badeventname'
    test_cases.append(
        NegativeAlertTestCase(
            description="Negative test case with bad eventName",
            events=[event],
        )
    )

    event = AlertTestSuite.create_event(default_event)
    event['_source']['utctimestamp'] = AlertTestSuite.subtract_from_timestamp_lambda({'minutes': 31})
    test_cases.append(
        NegativeAlertTestCase(
            description="Negative test case with old timestamp",
            events=[event],
        )
    )

    event = AlertTestSuite.create_event(default_event)
    event['_source']['errorCode'] = 'AccessDenied'
    test_cases.append(
        NegativeAlertTestCase(
            description="Negative test case with excluding errorCode",
            events=[event],
        )
    )
