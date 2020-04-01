from .positive_alert_test_case import PositiveAlertTestCase
from .negative_alert_test_case import NegativeAlertTestCase

from .alert_test_suite import AlertTestSuite


class TestAlertDeadman(AlertTestSuite):
    alert_filename = "deadman"
    alert_classname = "broNSM"
    deadman = True

    default_event = {
        "_source": {
            "hostname": "host1",
            "details": {
                "note": "MozillaAlive::Bro_Is_Watching_You"
            },
            "category": "bro",
            "source": "notice"
        }
    }

    default_alert = {
        "category": "deadman",
        "severity": "ERROR",
        "summary": 'No host1 bro healthcheck events found the past 20 minutes',
        "tags": ['bro', 'bro_deadman'],
    }

    test_cases = []

    event = AlertTestSuite.create_event(default_event)
    test_cases.append(
        NegativeAlertTestCase(
            description="Negative test case with good event",
            events=[event],
        )
    )

    event = AlertTestSuite.create_event(default_event)
    event['_source']['utctimestamp'] = AlertTestSuite.subtract_from_timestamp_lambda({'minutes': 21})
    event['_source']['receivedtimestamp'] = AlertTestSuite.subtract_from_timestamp_lambda({'minutes': 21})
    test_cases.append(
        PositiveAlertTestCase(
            description="Positive test case with old event",
            events=[event],
            expected_alert=default_alert
        )
    )

    event = AlertTestSuite.create_event(default_event)
    event['_source']['hostname'] = "host4"
    test_cases.append(
        PositiveAlertTestCase(
            description="Positive test case with incorrect host",
            events=[event],
            expected_alert=default_alert
        )
    )

    event = AlertTestSuite.create_event(default_event)
    event['_source']['details']['note'] = "some note"
    test_cases.append(
        PositiveAlertTestCase(
            description="Positive test case with bad note",
            events=[event],
            expected_alert=default_alert
        )
    )

    event = AlertTestSuite.create_event(default_event)
    event['_source']['category'] = "somecategory"
    test_cases.append(
        PositiveAlertTestCase(
            description="Positive test case with bad category",
            events=[event],
            expected_alert=default_alert
        )
    )

    event = AlertTestSuite.create_event(default_event)
    event['_source']['source'] = "somesource"
    test_cases.append(
        PositiveAlertTestCase(
            description="Positive test case with bad source",
            events=[event],
            expected_alert=default_alert
        )
    )
