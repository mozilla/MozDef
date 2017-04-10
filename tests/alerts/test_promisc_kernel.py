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
            "hostname": "logging.server.com",
            "details": {
                "hostname": "random.hacked.server.yours",
            }
        }
    }

    # This alert is the expected result from running this task
    default_alert = {
        "category": "promisc",
        "severity": "WARNING",
        "summary": "Promiscuous mode enabled on random.hacked.server.yours [10]",
        "tags": ['promisc', 'kernel'],
    }

    test_cases = []

    test_cases.append(
        PositiveAlertTestCase(
            description="Positive test case with good event",
            events=[AlertTestSuite.create_event(default_event)],
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
    event['_type'] = 'audit'
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
            description="Negative test case with bad eventName",
            events=[event],
        )
    )

    event = AlertTestSuite.create_event(default_event)
    event['_source']['summary'] = 'Promisc: Interface eth0 set promiscuous off'
    test_cases.append(
        NegativeAlertTestCase(
            description="Negative test case with bad summary",
            events=[event],
        )
    )

    event = AlertTestSuite.create_event(default_event)
    event['_source']['summary'] = 'device vethc0c001e entered promiscuous mode'
    test_cases.append(
        NegativeAlertTestCase(
            description="Negative test case with a bad interface",
            events=[event],
        )
    )

    event = AlertTestSuite.create_event(default_event)
    event['_source']['utctimestamp'] = AlertTestSuite.subtract_from_timestamp_lambda({'minutes': 3})
    test_cases.append(
        NegativeAlertTestCase(
            description="Negative test case with old timestamp",
            events=[event],
        )
    )
