from positive_alert_test_case import PositiveAlertTestCase
from negative_alert_test_case import NegativeAlertTestCase

from alert_test_suite import AlertTestSuite

class TestPromiscKernel(AlertTestSuite):
    alert_filename = "promisc_kernel"

    # This event is the default positive event that will cause the
    # alert to trigger
    default_event = {
        "_type": "event",
        "_source": {
            "category": "syslog",
            "summary": "device eth0 entered promiscuous mode",
            "hostname": "test1.host.domain.com",
        }
    }

    # This alert is the expected result from running this task
    default_alert = {
        "category": "promisc",
        "severity": "CRITICAL",
        "summary": "Promiscuous mode enabled on test1.host.domain.com",
        "tags": ['promisc', 'kernel'],
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
                        "utctimestamp": AlertTestSuite.subtract_from_timestamp_lambda({'minutes': 1})
                    }
                }
            ],
            expected_alert=default_alert
        ),

        NegativeAlertTestCase(
            description="Negative test case with bad event type",
            events=[
                {
                    "_type": "audit",
                }
            ],
        ),

        NegativeAlertTestCase(
            description="Negative test case with bad eventName",
            events=[
                {
                    "_source": {
                        "category": "badcategory",
                    }
                }
            ],
        ),

        NegativeAlertTestCase(
            description="Negative test case with bad summary",
            events=[
                {
                    "_source": {
                        "summary": "Promisc: Interface eth0 set promiscuous off",
                    }
                }
            ],
        ),

        NegativeAlertTestCase(
            description="Negative test case with a bad interface",
            events=[
                {
                    "_source": {
                        "summary": "device vethc0c001e entered promiscuous mode",
                    }
                }
            ],
        ),

        NegativeAlertTestCase(
            description="Negative test case with old timestamp",
            events=[
                {
                    "_source": {
                        "utctimestamp": AlertTestSuite.subtract_from_timestamp_lambda({'minutes': 3})
                    }
                }
            ],
        ),
    ]
