from positive_alert_test_case import PositiveAlertTestCase
from negative_alert_test_case import NegativeAlertTestCase

from alert_test_suite import AlertTestSuite


class TestAlertCloudtrailDeadman(AlertTestSuite):
    alert_filename = "cloudtrail_deadman"

    # This event is the default positive event that will cause the
    # alert to trigger
    default_event = {
        "_type": "cloudtrail",
        "_source": {
            "eventName": "somename"
        }
    }

    # This alert is the expected result from running this task
    default_alert = {
        "category": "deadman",
        "severity": "ERROR",
        "summary": 'No cloudtrail events found the last hour',
        "tags": ['cloudtrail', 'aws'],
    }

    test_cases = [
        PositiveAlertTestCase(
            description="Positive test case with good event",
            events=[
                {
                    "_source": {
                        "utctimestamp": AlertTestSuite.subtract_from_timestamp_lambda({'hours': 2}),
                    }
                }
            ],
            expected_alert=default_alert
        ),

        PositiveAlertTestCase(
            description="Postive test case with bad event type",
            events=[
                {
                    "_type": "event",
                }
            ],
            expected_alert=default_alert
        ),

        NegativeAlertTestCase(
            description="Negative test case with old timestamp",
            events=[
                {
                    "_source": {
                        "utctimestamp": AlertTestSuite.subtract_from_timestamp_lambda({'minutes': 30})
                    }
                }
            ],
        ),
    ]
