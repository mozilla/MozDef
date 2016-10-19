from positive_alert_test_case import PositiveAlertTestCase
from negative_alert_test_case import NegativeAlertTestCase

from alert_test_suite import AlertTestSuite


class TestAlertCorrelatedIntelNotice(AlertTestSuite):
    alert_filename = "correlated_alerts_pyes"

    # This event is the default positive event that will cause the
    # alert to trigger
    default_event = {
        "_type": "bro",
        "_source": {
            "summary": 'CrowdStrike::Correlated_Alerts Host 1.2.3.4 caused an alert to throw',
            "eventsource": "nsm",
            "category": "bronotice",
            "details": {
                "sourceipaddress": "1.2.3.4",
                "note": "CrowdStrike::Correlated_Alerts example alert",
            }
        }
    }

    # This alert is the expected result from running this task
    default_alert = {
        "category": "correlatedalerts",
        "severity": "NOTICE",
        "summary": "exhostname CrowdStrike::Correlated_Alerts Host 1.2.3.4 caused an alert to throw",
        "tags": ['nsm,bro,correlated'],
        "url": "https://mana.mozilla.org/wiki/display/SECURITY/NSM+IR+procedures"
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
                        "utctimestamp": AlertTestSuite.subtract_from_timestamp_lambda({'minutes': 14})
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
            description="Negative test case with bad event source",
            events=[
                {
                    "_source": {
                        "eventsource": "bades",
                    }
                }
            ],
        ),

        NegativeAlertTestCase(
            description="Negative test case with bad category",
            events=[
                {
                    "_source": {
                        "category": "badcategory"
                    }
                }
            ],
        ),

        NegativeAlertTestCase(
            description="Negative test case with non existing sourceipaddress",
            events=[
                {
                    "_source": {
                        "details": {
                            "sourceipaddress": None
                        }
                    }
                }
            ],
        ),

        NegativeAlertTestCase(
            description="Negative test case with bad note",
            events=[
                {
                    "_source": {
                        "details": {
                            "note": "bad note here"
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
                        "utctimestamp": AlertTestSuite.subtract_from_timestamp_lambda({'minutes': 16})
                    }
                }
            ],
        ),
    ]
