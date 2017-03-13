from positive_alert_test_case import PositiveAlertTestCase
from negative_alert_test_case import NegativeAlertTestCase

from alert_test_suite import AlertTestSuite

class TestSessionOpenedCrit(AlertTestSuite):
    alert_filename = "session_opened_critical"

    # This event is the default positive event that will cause the
    # alert to trigger
    default_event = {
        "_type": "event",
        "_source": {
            "category": "syslog",
            "summary": "pam_unix(sshd:session): session opened for user mpurzynski by (uid=0)",
            "details": {
                "hostname": "nsmserver1.private.scl3.mozilla.com",
            }
        }
    }

    # This alert is the expected result from running this task
    default_alert = {
        "category": "session",
        "severity": "CRITICAL",
        "summary": "Session opened on nsmserver1.private.scl3.mozilla.com",
        "tags": ['pam', 'syslog'],
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
                        "summary": "session closed",
                    }
                }
            ],
        ),

        NegativeAlertTestCase(
            description="Negative test case with bad details.hostname",
            events=[
                {
                    "_source": {
                        "details": {
                            "hostname": "mozdefes7.private.scl3.mozilla.com",
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
