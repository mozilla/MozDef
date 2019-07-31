from .positive_alert_test_case import PositiveAlertTestCase
from .negative_alert_test_case import NegativeAlertTestCase

from .alert_test_suite import AlertTestSuite


class TestOldEvents(AlertTestSuite):
    # We just create a stub, so that we can replace timestamp fields
    default_event = {
        "_source": {}
    }

    default_alert = {
        "category": "maintenance",
        "severity": "ERROR",
        "tags": ['pipeline'],
        "summary": "Events have an outdated utctimestamp",
    }

    test_cases = []

    events = AlertTestSuite.create_events(default_event, 100)
    temp_alert = AlertTestSuite.copy(default_alert)
    temp_alert['summary'] = 'Events have an outdated utctimestamp (100)'
    for event in events:
        event['_source']['utctimestamp'] = AlertTestSuite.subtract_from_timestamp_lambda({'hours': 25})
    test_cases.append(
        PositiveAlertTestCase(
            description="Positive test case with good events",
            events=events,
            expected_alert=temp_alert
        )
    )

    event = AlertTestSuite.create_event(default_event)
    event['_source']['utctimestamp'] = AlertTestSuite.subtract_from_timestamp_lambda({'hours': 25})
    temp_alert = AlertTestSuite.copy(default_alert)
    temp_alert['summary'] = 'Events have an outdated utctimestamp (1)'
    test_cases.append(
        PositiveAlertTestCase(
            description="Positive test case with good event",
            events=[event],
            expected_alert=temp_alert
        )
    )

    event = AlertTestSuite.create_event(default_event)
    test_cases.append(
        NegativeAlertTestCase(
            description="Negative test case with event with recent utctimestamp",
            events=[event],
        )
    )

    events = AlertTestSuite.create_events(default_event, 100)
    test_cases.append(
        NegativeAlertTestCase(
            description="Negative test case with events with recent utctimestamp",
            events=events,
        )
    )

    event = AlertTestSuite.create_event(default_event)
    event['_source']['utctimestamp'] = AlertTestSuite.subtract_from_timestamp_lambda({'hours': 25})
    event['_source']['receivedtimestamp'] = AlertTestSuite.subtract_from_timestamp_lambda({'hours': 25})
    test_cases.append(
        NegativeAlertTestCase(
            description="Negative test case with event with old utctimestamp and receivedtimestamp",
            events=[event],
        )
    )
