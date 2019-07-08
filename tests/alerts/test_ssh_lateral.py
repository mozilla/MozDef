from .positive_alert_test_case import PositiveAlertTestCase
from .negative_alert_test_case import NegativeAlertTestCase

from .alert_test_suite import AlertTestSuite


class TestSSHLateral(AlertTestSuite):
    alert_filename = 'ssh_lateral'
    alert_classname = 'SshLateral'

    # This event is the default positive event that will cause the
    # alert to trigger
    default_event = {
        '_source': {
            'category': 'syslog',
            'hostname': 'test-host.enterprise.mozilla.com',
            'summary': 'Accepted publickey for user1 from 10.2.3.4 port 19936 ssh2: RSA SHA256:ET72afGGbxabDersgSdQ+xJYB6ILXOFSDsLsTqDs',
            'details': {
                'program': 'sshd'
            }
        }
    }

    # This alert is the expected result from running this task
    default_alert = {
        'category': 'session',
        'severity': 'WARNING',
        'summary': 'SSH lateral movement outside policy: access to test-host.enterprise.mozilla.com from 10.2.3.4 (mock_hostname1.mozilla.org) as user1',
        'tags': ['sshd', 'syslog'],
    }

    test_cases = []

    test_cases.append(
        PositiveAlertTestCase(
            description='Positive test case with good event',
            events=[AlertTestSuite.create_event(default_event)],
            expected_alert=default_alert
        )
    )

    event = AlertTestSuite.create_event(default_event)
    event['_source']['category'] = 'bad'
    test_cases.append(
        NegativeAlertTestCase(
            description="Negative test case with bad event category",
            events=[event],
        )
    )

    event = AlertTestSuite.create_event(default_event)
    event['_source']['summary'] = 'some bad summary'
    test_cases.append(
        NegativeAlertTestCase(
            description="Negative test case with bad event summary",
            events=[event],
        )
    )

    event = AlertTestSuite.create_event(default_event)
    event['_source']['details']['program'] = 'ftpd'
    test_cases.append(
        NegativeAlertTestCase(
            description="Negative test case with bad event details.program",
            events=[event],
        )
    )

    event = AlertTestSuite.create_event(default_event)
    event['_source']['utctimestamp'] = AlertTestSuite.subtract_from_timestamp_lambda({'minutes': 16})
    event['_source']['receivedtimestamp'] = AlertTestSuite.subtract_from_timestamp_lambda({'minutes': 16})
    test_cases.append(
        NegativeAlertTestCase(
            description="Negative test case with an event with old timestamp",
            events=[event],
        )
    )
