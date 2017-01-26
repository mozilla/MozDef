from positive_alert_test_case import PositiveAlertTestCase
from negative_alert_test_case import NegativeAlertTestCase

from alert_test_suite import AlertTestSuite


class TestAlertOpenPortViolation(AlertTestSuite):
    alert_filename = "open_port_violation"

    # This event is the default positive event that will cause the
    # alert to trigger
    default_event = {
        "_type": "event",
        "_source": {
            "tags": ["open_port_policy_violation"],
            "details": {
                "destinationipaddress": "220.231.44.213",
                "destinationport": 25,
            }
        }
    }

    # This alert is the expected result from running this task
    default_alert = {
        "category": "open_port_policy_violation",
        "tags": ['open_port_policy_violation'],
        "severity": "CRITICAL",
        "summary": '10 unauthorized open port(s) on 220.231.44.213 (25 25 25 25 25 )',
    }

    test_cases = []

    default_events = list()
    for num in xrange(10):
        default_events.append(AlertTestSuite.copy(default_event))

    test_cases.append(
        PositiveAlertTestCase(
            description="Positive test with default events and default alert expected",
            events=default_events,
            expected_alert=default_alert
        )
    )

    custom_events = default_events
    for temp_event in custom_events:
        temp_event['_source']['utctimestamp'] = AlertTestSuite.subtract_from_timestamp_lambda(date_timedelta={'minutes': 239})
    test_cases.append(
        PositiveAlertTestCase(
            description="Positive test with events a minute earlier",
            events=custom_events,
            expected_alert=default_alert
        )
    )

    custom_events = default_events
    for temp_event in custom_events:
        temp_event['_type'] = 'bad'
    test_cases.append(
        NegativeAlertTestCase(
            description="Negative test case with events with incorrect _type",
            events=custom_events,
        )
    )

    custom_events = default_events
    for temp_event in custom_events:
        temp_event['_source']['tags'] = 'bad tag example'
    test_cases.append(
        NegativeAlertTestCase(
            description="Negative test case with events with incorrect tags",
            events=custom_events,
        )
    )

    custom_events = default_events
    for temp_event in custom_events:
        temp_event['_source']['utctimestamp'] = AlertTestSuite.subtract_from_timestamp_lambda({'minutes': 241})
    test_cases.append(
        NegativeAlertTestCase(
            description="Negative test case with old timestamp",
            events=custom_events,
        )
    )
