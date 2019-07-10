from .positive_alert_test_case import PositiveAlertTestCase
from .negative_alert_test_case import NegativeAlertTestCase

from .alert_test_suite import AlertTestSuite


class TestAlertDuoFailOpen(AlertTestSuite):
    alert_filename = "duo_fail_open"

    # This event is the default positive event that will cause the
    # alert to trigger
    default_event = {
        "_source": {
            "summary": 'Failsafe Duo login by 1.2.3.4',
        }
    }

    # This alert is the expected result from running this task
    default_alert = {
        "category": "bypass",
        "tags": ['openvpn', 'duosecurity'],
        "severity": "WARNING",
        "summary": "DuoSecurity contact failed, fail open triggered on exhostname",
    }

    test_cases = []

    test_cases.append(
        PositiveAlertTestCase(
            description="Positive test with default events and default alert expected",
            events=AlertTestSuite.create_events(default_event, 10),
            expected_alert=default_alert
        )
    )

    test_cases.append(
        PositiveAlertTestCase(
            description="Positive test with one default event and default alert expected",
            events=AlertTestSuite.create_events(default_event, 1),
            expected_alert=default_alert
        )
    )

    events = AlertTestSuite.create_events(default_event, 10)
    for event in events:
        event['_source']['utctimestamp'] = AlertTestSuite.subtract_from_timestamp_lambda(date_timedelta={'minutes': 14})
        event['_source']['receivedtimestamp'] = AlertTestSuite.subtract_from_timestamp_lambda(date_timedelta={'minutes': 14})
    test_cases.append(
        PositiveAlertTestCase(
            description="Positive test with events a minute earlier",
            events=events,
            expected_alert=default_alert
        )
    )

    events = AlertTestSuite.create_events(default_event, 10)
    for event in events:
        event['_source']['summary'] = 'bad summary example'
    test_cases.append(
        NegativeAlertTestCase(
            description="Negative test case with events with incorrect summary",
            events=events,
        )
    )

    events = AlertTestSuite.create_events(default_event, 10)
    for event in events:
        event['_source']['utctimestamp'] = AlertTestSuite.subtract_from_timestamp_lambda({'minutes': 16})
        event['_source']['receivedtimestamp'] = AlertTestSuite.subtract_from_timestamp_lambda({'minutes': 16})
    test_cases.append(
        NegativeAlertTestCase(
            description="Negative test case with old timestamp",
            events=events,
        )
    )
