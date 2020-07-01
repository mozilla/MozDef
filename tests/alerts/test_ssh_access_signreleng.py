from .positive_alert_test_case import PositiveAlertTestCase
from .negative_alert_test_case import NegativeAlertTestCase

from .alert_test_suite import AlertTestSuite


class TestAlertSSHAccessSignReleng(AlertTestSuite):
    alert_classname = "AlertAuthSignRelengSSH"
    alert_filename = "ssh_access_signreleng"

    # This event is the default positive event that will cause the
    # alert to trigger
    default_event = {
        "_source": {
            "tags": ["releng"],
            "hostname": 'host1',
            "summary": 'Accepted publickey for ttesterson from 1.2.3.4 port 39190 ssh2',
            "details": {
                "sourceipaddress": "1.2.3.4",
                "program": 'sshd'
            }
        }
    }

    # This alert is the expected result from running this task
    default_alert = {
        "category": "access",
        "severity": "NOTICE",
        "summary": "SSH login from 1.2.3.4 on host1 as user ttesterson",
        "tags": ['ssh'],
        'channel': '#somechannel',
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
    event['_source']['summary'] = 'Accepted publickey for someuser from 1.2.3.4 port 39190 ssh2'
    alert = AlertTestSuite.create_alert(default_alert)
    alert['summary'] = 'SSH login from 1.2.3.4 on host1 as user someuser'
    test_cases.append(
        PositiveAlertTestCase(
            description="Positive test case with good event with excluded user but not ip",
            events=[event],
            expected_alert=alert
        )
    )

    event = AlertTestSuite.create_event(default_event)
    event['_source']['details']['sourceipaddress'] = '4.5.6.7'
    alert = AlertTestSuite.create_alert(default_alert)
    alert['summary'] = 'SSH login from 4.5.6.7 on host1 as user ttesterson'
    test_cases.append(
        PositiveAlertTestCase(
            description="Positive test case with good event with excluded ip but not user",
            events=[event],
            expected_alert=alert
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
    event['_source']['tags'] = ['badtag']
    test_cases.append(
        NegativeAlertTestCase(
            description="Negative test case with bad tags",
            events=[event],
        )
    )

    event = AlertTestSuite.create_event(default_event)
    event['_source']['details']['program'] = 'badprogram'
    test_cases.append(
        NegativeAlertTestCase(
            description="Negative test case with bad program",
            events=[event],
        )
    )

    event = AlertTestSuite.create_event(default_event)
    event['_source']['hostname'] = 'badhostname'
    test_cases.append(
        NegativeAlertTestCase(
            description="Negative test case with bad hostname",
            events=[event],
        )
    )

    event = AlertTestSuite.create_event(default_event)
    event['_source']['summary'] = 'bad summary'
    test_cases.append(
        NegativeAlertTestCase(
            description="Negative test case with bad summary",
            events=[event],
        )
    )

    event = AlertTestSuite.create_event(default_event)
    event['_source']['summary'] = 'Accepted publickey for someuser from 4.5.6.7 port 39190 ssh2'
    event['_source']['details']['sourceipaddress'] = '4.5.6.7'
    test_cases.append(
        NegativeAlertTestCase(
            description="Negative test case with good event with excluded user and ip",
            events=[event],
        )
    )

    event = AlertTestSuite.create_event(default_event)
    event['_source']['summary'] = 'Accepted publickey for anotheruser from 8.9.10.11 port 39190 ssh2'
    event['_source']['details']['sourceipaddress'] = '8.9.10.11'
    test_cases.append(
        NegativeAlertTestCase(
            description="Negative test case with good event with excluded user and ip from second index",
            events=[event],
        )
    )

    event = AlertTestSuite.create_event(default_event)
    event['_source']['summary'] = '[12345] Accepted publickey for ttesterson from 1.2.3.4 port 39190 ssh2'
    test_cases.append(
        PositiveAlertTestCase(
            description="Positive test case with processid at beginning of summary",
            events=[event],
            expected_alert=default_alert
        )
    )
