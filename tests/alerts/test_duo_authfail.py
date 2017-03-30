from positive_alert_test_case import PositiveAlertTestCase
from negative_alert_test_case import NegativeAlertTestCase

from alert_test_suite import AlertTestSuite


class TestAlertDuoAuthFail(AlertTestSuite):
    alert_filename = "duo_authfail"

    # This event is the default positive event that will cause the
    # alert to trigger
    default_event = {
        "_type": "event",
        "_source": {
            "category": "event",
            "summary": 'authentication FRAUD for you@somewhere.com',
            "details": {
                "sourceipaddress": "1.2.3.4",
                "username": "you@somewhere.com",
                "result": "FRAUD",
            }
        }
    }

    # This alert is the expected result from running this task
    default_alert = {
        "category": "duosecurity",
        "tags": ['duosecurity'],
        "severity": "WARNING",
        "url": "https://your.super.cool.documentation",
        "summary": "Duo Authentication Failure: user you@somewhere.com rejected and marked a Duo Authentication attempt from 1.2.3.4 as fraud",
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
                    "_type": "wrongtype",
                }
            ],
        ),

        NegativeAlertTestCase(
            description="Negative test case with bad category",
            events=[
                {
                    "_source": {
                        "category": "badcategory",
                    }
                }
            ],
        ),

        NegativeAlertTestCase(
            description="Negative test case with bad result",
            events=[
                {
                    "_source": {
                        "details": {
                            "result": "SUCCESS",
                        }
                    }
                }
            ],
        ),

        NegativeAlertTestCase(
            description="Negative test case without the details.sourceipaddress",
            events=[
                {
                    "_source": {
                        "details": {
                            "sourceipaddress": None,
                        }
                    }
                }
            ],
        ),

        NegativeAlertTestCase(
            description="Negative test case without the details.username",
            events=[
                {
                    "_source": {
                        "details": {
                            "username": None,
                        }
                    }
                }
            ],
        ),

        NegativeAlertTestCase(
            description="Negative test case with a wrong timestamp",
            events=[
                {
                    "_source": {
                        "utctimestamp": AlertTestSuite.subtract_from_timestamp_lambda({'minutes': 3})
                    }
                }
            ],
        ),
    ]
