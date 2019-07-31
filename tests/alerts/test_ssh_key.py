from .positive_alert_test_case import PositiveAlertTestCase
from .negative_alert_test_case import NegativeAlertTestCase

from .alert_test_suite import AlertTestSuite


class TestSSHKey(AlertTestSuite):
    alert_filename = 'ssh_key'
    alert_classname = 'SSHKey'

    # This event is the default positive event that will cause the
    # alert to trigger
    default_event = {
        '_source': {
            'category': 'event',
            'processid': '19690',
            'severity': 'INFO',
            'tags': [
                'mig-runner-sshkey'
            ],
            'hostname': 'mig-runner-host.mozilla.com',
            'mozdefhostname': 'mozdef-host.mozilla.com',
            'summary': 'MIG sshkey module result for key-host.mozilla.com',
            'processname': '/home/migrunner/runner/plugins/sshkeyplugin.py',
            'details': {
                'authorizedkeys': [
                    {
                        'fingerprint_sha256': 'SHA256:AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA',
                        'encrypted': False,
                        'fingerprint_md5': '00:00:00:00:00:00:00:00:00:00:00:00:00:00:00:00',
                        'path': '/home/user/.ssh/authorized_keys'
                    }
                ],
                'private': [
                    {
                        'fingerprint_sha256': 'SHA256:AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA',
                        'encrypted': False,
                        'fingerprint_md5': '00:00:00:00:00:00:00:00:00:00:00:00:00:00:00:00',
                        'path': '/home/user/.ssh/id_rsa'
                    },
                    {
                        'fingerprint_sha256': 'SHA256:BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB',
                        'encrypted': False,
                        'fingerprint_md5': '11:11:11:11:11:11:11:11:11:11:11:11:11:11:11:11',
                        'path': '/home/user2/.ssh/id_rsa'
                    }
                ],
                'agent': 'key-host.mozilla.com',
            }
        }
    }

    # This alert is the expected result from running this task
    default_alert = {
        'category': 'sshkey',
        'severity': 'WARNING',
        'summary': 'Private keys detected on key-host.mozilla.com missing from whitelist',
        'tags': ['sshkey'],
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
    event['_source']['details']['agent'] = 'somehost.ignorehosts.com'
    event['_source']['details']['private'] = [
        {
            'fingerprint_sha256': 'SHA256:AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA',
            'encrypted': False,
            'fingerprint_md5': '00:00:00:00:00:00:00:00:00:00:00:00:00:00:00:00',
            'path': '/home/user/.ssh/id_rsa'
        }
    ]
    test_cases.append(
        NegativeAlertTestCase(
            description='Whitelist test with default configuration file',
            events=[event],
        )
    )

    event = AlertTestSuite.create_event(default_event)
    event['_source']['details']['agent'] = 'somehost.ignorehosts.com'
    event['_source']['details']['private'] = [
        {
            'fingerprint_sha256': 'SHA256:AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA',
            'encrypted': False,
            'fingerprint_md5': '00:00:00:00:00:00:00:00:00:00:00:00:00:00:00:00',
            'path': '/home/user2/.ssh/id_rsa'
        }
    ]
    specific_alert = default_alert.copy()
    specific_alert['summary'] = 'Private keys detected on somehost.ignorehosts.com missing from whitelist'
    test_cases.append(
        PositiveAlertTestCase(
            description='Whitelist test with default configuration file, only host matches',
            events=[event],
            expected_alert=specific_alert
        )
    )
