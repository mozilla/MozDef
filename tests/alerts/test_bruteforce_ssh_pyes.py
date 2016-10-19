from positive_alert_test_case import PositiveAlertTestCase
from negative_alert_test_case import NegativeAlertTestCase

from alert_test_suite import AlertTestSuite


class TestAlertBruteforceSshES(AlertTestSuite):
    alert_filename = "bruteforce_ssh_pyes"

    # This event is the default positive event that will cause the
    # alert to trigger
    default_event = {
        "_type": "event",
        "_source": {
            "summary": 'login invalid ldap_count_entries failed by 1.2.3.4',
            "program": "sshd",
            "details": {
                "hostname": "exhostname",
                "sourceipaddress": "1.2.3.4",
            }
        }
    }

    # This alert is the expected result from running this task
    default_alert = {
        "category": "bruteforce",
        "severity": "NOTICE",
        "summary": "10 ssh bruteforce attempts by 1.2.3.4 exhostname (10 hits)",
        "tags": ['ssh']
    }

    test_cases = []

    default_events = list()
    for num in xrange(10):
        default_events.append(AlertTestSuite.copy(default_event))


    custom_events = default_events
    test_cases.append(
        PositiveAlertTestCase(
            description="Positive test with default event and default alert expected",
            events=custom_events,
            expected_alert=default_alert
        )
    )

    custom_events = default_events
    for temp_event in custom_events:
        temp_event['_source']['utctimestamp'] = AlertTestSuite.subtract_from_timestamp_lambda(date_timedelta={'minutes': 1})
    test_cases.append(
        PositiveAlertTestCase(
            description="Positive test with events a minute earlier",
            events=custom_events,
            expected_alert=default_alert
        )
    )

    custom_events = default_events
    for temp_event in custom_events:
        temp_event['_source']['summary'] = 'login failed'
    test_cases.append(
        PositiveAlertTestCase(
            description="Positive test with events with a summary of 'login failed'",
            events=custom_events,
            expected_alert=default_alert
        )
    )

    custom_events = default_events
    for temp_event in custom_events:
        temp_event['_source']['summary'] = 'invalid failed'
    test_cases.append(
        PositiveAlertTestCase(
            description="Positive test with events with a summary of 'invalid failed'",
            events=custom_events,
            expected_alert=default_alert
        )
    )

    custom_events = default_events
    for temp_event in custom_events:
        temp_event['_source']['summary'] = 'invalid failed'
    test_cases.append(
        PositiveAlertTestCase(
            description="Positive test with events with a summary of 'ldap_count_entries failed'",
            events=custom_events,
            expected_alert=default_alert
        )
    )

    custom_events = default_events
    custom_events[8]['_source']['details']['sourceipaddress'] = "127.0.0.1"
    custom_events[9]['_source']['details']['sourceipaddress'] = "127.0.0.1"
    test_cases.append(
        NegativeAlertTestCase(
            description="Negative test case with 10 events however one has different sourceipaddress",
            events=custom_events,
        )
    )

    test_cases.append(
        NegativeAlertTestCase(
            description="Negative test case with not enough events",
            events=[default_event],
        ),
    )

    custom_events = default_events
    for temp_event in custom_events:
        temp_event['_source']['summary'] = 'login good ldap_count_entries'
    test_cases.append(
        NegativeAlertTestCase(
            description="Negative test case with events with summary without 'failed'",
            events=custom_events,
        )
    )

    custom_events = default_events
    for temp_event in custom_events:
        temp_event['_source']['summary'] = 'failed'
    test_cases.append(
        NegativeAlertTestCase(
            description="Negative test case with events with summary with only 'failed'",
            events=custom_events,
        )
    )

    custom_events = default_events
    for temp_event in custom_events:
        temp_event['_source']['summary'] = 'login'
    test_cases.append(
        NegativeAlertTestCase(
            description="Negative test case with events with summary with only 'login'",
            events=custom_events,
        )
    )

    custom_events = default_events
    for temp_event in custom_events:
        temp_event['_source']['summary'] = 'invalid'
    test_cases.append(
        NegativeAlertTestCase(
            description="Negative test case with events with summary with only 'invalid'",
            events=custom_events,
        )
    )

    custom_events = default_events
    for temp_event in custom_events:
        temp_event['_source']['summary'] = 'ldap_count_entries'
    test_cases.append(
        NegativeAlertTestCase(
            description="Negative test case with events with summary with only 'ldap_count_entries'",
            events=custom_events,
        )
    )

    custom_events = default_events
    for temp_event in custom_events:
        temp_event['_source']['program'] = 'badprogram'
    test_cases.append(
        NegativeAlertTestCase(
            description="Negative test case with events with bad program",
            events=custom_events,
        )
    )

    custom_events = default_events
    for temp_event in custom_events:
        temp_event['_source']['utctimestamp'] = AlertTestSuite.subtract_from_timestamp_lambda({'minutes': 3})
    test_cases.append(
        NegativeAlertTestCase(
            description="Negative test case with old timestamp",
            events=custom_events,
        )
    )

    custom_events = default_events
    for temp_event in custom_events:
        temp_event['_source']['summary'] = temp_event['_source']['summary'].replace('1.2.3.4', '10.22.75.203')
    test_cases.append(
        NegativeAlertTestCase(
            description="Negative test case with 10.22.75.203 as a whitelisted ip",
            events=custom_events,
        )
    )

    custom_events = default_events
    for temp_event in custom_events:
        temp_event['_source']['summary'] = temp_event['_source']['summary'].replace('1.2.3.4', '10.8.75.144')
    test_cases.append(
        NegativeAlertTestCase(
            description="Negative test case with 10.8.75.144 as a whitelisted ip",
            events=custom_events,
        )
    )
