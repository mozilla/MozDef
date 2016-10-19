from positive_alert_test_case import PositiveAlertTestCase
from negative_alert_test_case import NegativeAlertTestCase

from alert_test_suite import AlertTestSuite


class TestAlertDuoFailOpen(AlertTestSuite):
    alert_filename = "duo_fail_open"

    # This event is the default positive event that will cause the
    # alert to trigger
    default_event = {
        "_type": "event",
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

    test_cases.append(
        PositiveAlertTestCase(
            description="Positive test with one default event and default alert expected",
            events=[default_event],
            expected_alert=default_alert
        )
    )

    custom_events = default_events
    for temp_event in custom_events:
        temp_event['_source']['utctimestamp'] = AlertTestSuite.subtract_from_timestamp_lambda(date_timedelta={'minutes': 14})
    test_cases.append(
        PositiveAlertTestCase(
            description="Positive test with events a minute earlier",
            events=custom_events,
            expected_alert=default_alert
        )
    )

    custom_events = default_events
    for temp_event in custom_events:
        temp_event['_source']['summary'] = 'bad summary example'
    test_cases.append(
        NegativeAlertTestCase(
            description="Negative test case with events with incorrect summary",
            events=custom_events,
        )
    )

    custom_events = default_events
    for temp_event in custom_events:
        temp_event['_source']['utctimestamp'] = AlertTestSuite.subtract_from_timestamp_lambda({'minutes': 16})
    test_cases.append(
        NegativeAlertTestCase(
            description="Negative test case with old timestamp",
            events=custom_events,
        )
    )
