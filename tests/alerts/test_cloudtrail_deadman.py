from .positive_alert_test_case import PositiveAlertTestCase
from .negative_alert_test_case import NegativeAlertTestCase

from .alert_test_suite import AlertTestSuite


class TestAlertCloudtrailDeadman(AlertTestSuite):
    alert_filename = "cloudtrail_deadman"
    deadman = True

    # This event is the default positive event that will cause the
    # alert to trigger
    default_event = {
        "_source": {
            "eventName": "somename",
            "source": "cloudtrail"
        }
    }

    # This alert is the expected result from running this task
    default_alert = {
        "category": "deadman",
        "severity": "ERROR",
        "summary": 'No cloudtrail events found the last hour',
        "tags": ['cloudtrail', 'aws'],
    }

    test_cases = []

    event = AlertTestSuite.create_event(default_event)
    event['_source']['utctimestamp'] = AlertTestSuite.subtract_from_timestamp_lambda({'hours': 2})
    event['_source']['receivedtimestamp'] = AlertTestSuite.subtract_from_timestamp_lambda({'hours': 2})
    test_cases.append(
        PositiveAlertTestCase(
            description="Positive test case with good event",
            events=[event],
            expected_alert=default_alert
        )
    )

    event = AlertTestSuite.create_event(default_event)
    event['_source']['source'] = 'event'
    test_cases.append(
        PositiveAlertTestCase(
            description="Positive test case with bad event source",
            events=[event],
            expected_alert=default_alert
        )
    )

    event = AlertTestSuite.create_event(default_event)
    event['_source']['utctimestamp'] = AlertTestSuite.subtract_from_timestamp_lambda({'minutes': 30})
    event['_source']['receivedtimestamp'] = AlertTestSuite.subtract_from_timestamp_lambda({'minutes': 30})
    test_cases.append(
        NegativeAlertTestCase(
            description="Negative test case with old timestamp",
            events=[event],
        )
    )
