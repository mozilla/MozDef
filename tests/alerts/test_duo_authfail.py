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
    event['_source']['utctimestamp'] = AlertTestSuite.subtract_from_timestamp_lambda({'minutes': 1})
    test_cases.append(
        PositiveAlertTestCase(
            description="Positive test case with an event with somewhat old timestamp",
            events=[event],
            expected_alert=default_alert
        )
    )

    event = AlertTestSuite.create_event(default_event)
    event['_type'] = 'wrongtype'
    test_cases.append(
        NegativeAlertTestCase(
            description="Negative test case with bad event type",
            events=[event],
        )
    )

    event = AlertTestSuite.create_event(default_event)
    event['_source']['category'] = 'badcategory'
    test_cases.append(
        NegativeAlertTestCase(
            description="Negative test case with bad category",
            events=[event],
        )
    )

    event = AlertTestSuite.create_event(default_event)
    event['_source']['details']['result'] = 'SUCCESS'
    test_cases.append(
        NegativeAlertTestCase(
            description="Negative test case with bad result",
            events=[event],
        )
    )

    event = AlertTestSuite.create_event(default_event)
    event['_source']['details']['sourceipaddress'] = None
    test_cases.append(
        NegativeAlertTestCase(
            description="Negative test case without the details.sourceipaddress",
            events=[event],
        )
    )

    event = AlertTestSuite.create_event(default_event)
    event['_source']['details']['username'] = None
    test_cases.append(
        NegativeAlertTestCase(
            description="Negative test case without the details.username",
            events=[event],
        )
    )

    event = AlertTestSuite.create_event(default_event)
    event['_source']['utctimestamp'] = AlertTestSuite.subtract_from_timestamp_lambda({'minutes': 3})
    test_cases.append(
        NegativeAlertTestCase(
            description="Negative test case with a wrong timestamp",
            events=[event],
        )
    )
