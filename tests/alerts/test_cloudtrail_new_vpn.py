from positive_alert_test_case import PositiveAlertTestCase
from negative_alert_test_case import NegativeAlertTestCase

from alert_test_suite import AlertTestSuite


class TestAlertCorrelatedIntelNotice(AlertTestSuite):
    alert_src = "cloudtrail_new_vpn"
    alert_name = "AlertCloudtrailNewVPN"

    # This event is the default positive event that will cause the
    # alert to trigger
    default_event = {
        "_type": "cloudtrail",
        "_source": {
            "eventName": "CreateVpnConnection",
        }
    }

    # This alert is the expected result from running this task
    default_alert = {
        "category": "AWSCloudtrail",
        "severity": "ERROR",
        "summary": "New VPN Connection Created",
        "tags": ['cloudtrail', 'aws'],
    }

    test_cases = [
        PositiveAlertTestCase(
            description="Positive test case with good event",
            events=[default_event],
            expected_alert=default_alert
        ),

        PositiveAlertTestCase(
            description="Positive test case with an event with somewhat old timestamp",
            events=[
                {
                    "_source": {
                        "utctimestamp": AlertTestSuite.subtract_from_timestamp_lambda({'minutes': 29})
                    }
                }
            ],
            expected_alert=default_alert
        ),

        NegativeAlertTestCase(
            description="Negative test case with bad event type",
            events=[
                {
                    "_type": "event",
                }
            ],
        ),

        NegativeAlertTestCase(
            description="Negative test case with bad eventName",
            events=[
                {
                    "_source": {
                        "eventName": "Badeventname",
                    }
                }
            ],
        ),

        NegativeAlertTestCase(
            description="Negative test case with old timestamp",
            events=[
                {
                    "_source": {
                        "utctimestamp": AlertTestSuite.subtract_from_timestamp_lambda({'minutes': 31})
                    }
                }
            ],
        ),
    ]
