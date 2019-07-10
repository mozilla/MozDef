from .positive_alert_test_case import PositiveAlertTestCase
from .negative_alert_test_case import NegativeAlertTestCase

from .alert_test_suite import AlertTestSuite


class TestAlertSSHAccess(AlertTestSuite):
    alert_classname = "AlertSSHAccess"
    alert_filename = "ssh_access"

    # This event is the default positive event that will cause the
    # alert to trigger
    default_event = {
        "_source": {
            "category": "syslog",
            "hostname": 'victim1.small.corp.com',
            "summary": 'Accepted publickey for alamakota from 11.22.33.44 port 39190 ssh2',
            "details": {
                "sourceipaddress": "11.22.33.44",
                "program": "sshd",
                "username": "alamakota"
            }
        }
    }

    # This alert is the expected result from running this task
    default_alert = {
        "category": "access",
        "severity": "CRITICAL",
        "summary": "SSH login from 11.22.33.44 on victim1.small.corp.com as user alamakota",
        "tags": ['ssh'],
        "notify_mozdefbot": True
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
    event['_source']['details']['sourceipaddress'] = "11.22.33.45"
    newip_alert = default_alert.copy()
    newip_alert['summary'] = "SSH login from 11.22.33.45 on victim1.small.corp.com as user alamakota"
    test_cases.append(
        PositiveAlertTestCase(
            description="Positive test case from a different server",
            events=[event],
            expected_alert=newip_alert
        )
    )

    event = AlertTestSuite.create_event(default_event)
    event['_source']['utctimestamp'] = AlertTestSuite.subtract_from_timestamp_lambda({'minutes': 14})
    event['_source']['receivedtimestamp'] = AlertTestSuite.subtract_from_timestamp_lambda({'minutes': 14})
    test_cases.append(
        PositiveAlertTestCase(
            description="Positive test case with an event with somewhat old timestamp",
            events=[event],
            expected_alert=default_alert
        )
    )

    event = AlertTestSuite.create_event(default_event)
    event['_source']['utctimestamp'] = AlertTestSuite.subtract_from_timestamp_lambda({'minutes': 16})
    event['_source']['receivedtimestamp'] = AlertTestSuite.subtract_from_timestamp_lambda({'minutes': 16})
    test_cases.append(
        NegativeAlertTestCase(
            description="Negative test case with old timestamp",
            events=[event],
        )
    )

    event = AlertTestSuite.create_event(default_event)
    event['_source']['category'] = ['bro']
    test_cases.append(
        NegativeAlertTestCase(
            description="Negative test case with bad category",
            events=[event],
        )
    )

    event = AlertTestSuite.create_event(default_event)
    event['_source']['details']['program'] = 'ssh'
    test_cases.append(
        NegativeAlertTestCase(
            description="Negative test case with bad program",
            events=[event],
        )
    )

    event = AlertTestSuite.create_event(default_event)
    event['_source']['details']['sourceipaddress'] = '213.212.11.5'
    test_cases.append(
        NegativeAlertTestCase(
            description="Negative test case with the source IP address outside of the watchlist",
            events=[event],
        )
    )
