from positive_alert_test_case import PositiveAlertTestCase
from negative_alert_test_case import NegativeAlertTestCase

from alert_test_suite import AlertTestSuite

class TestPromiscAudit(AlertTestSuite):
    alert_filename = "promisc_audit"

    # This event is the default positive event that will cause the
    # alert to trigger
    default_event = {
        "_type": "auditd",
        "_source": {
            "category": "promiscuous",
            "summary": "Promisc: Interface eth0 set promiscuous on",
            "hostname": "example1.hostname.domain.com",
            "details": {
                "dev": "eth0",
            }
        }
    }

    # This alert is the expected result from running this task
    default_alert = {
        "category": "promisc",
        "severity": "CRITICAL",
        "summary": "Promiscuous mode enabled on example1.hostname.domain.com",
        "tags": ['promisc', 'audit'],
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
                    "_type": "event",
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
                        "details": {
                            "dev": "veth123abc",
                        }
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
