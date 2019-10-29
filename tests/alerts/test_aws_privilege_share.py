from .alert_test_suite import AlertTestSuite
from .negative_alert_test_case import NegativeAlertTestCase
from .positive_alert_test_case import PositiveAlertTestCase


class TestAlertAWSPrivilegeShare(AlertTestSuite):
    alert_filename = 'aws_privilege_share'

    default_event = {
        '_source': {
            'details': {
                'eventname': 'AttachUserPolicy',
                'requestparameters': {
                    'username': 'tester'
                },
                'useridentity': {
                    'sessioncontext': {
                        'sessionissuer': {
                            'username': 'InfosecAdmin'
                        }
                    }
                }
            }
        }
    }

    non_root_user_evt = {
        '_source': {
            'details': {
                'eventname': 'AttachUserPolicy',
                'requestparameters': {
                    'username': 'tester'
                },
                'useridentity': {
                    'sessioncontext': {
                        'sessionissuer': {
                            'username': 'NotAdmin'
                        }
                    }
                }
            }
        }
    }

    not_attach_policy_evt = {
        '_source': {
            'details': {
                'eventname': 'SomethingElse',
                'requestparameters': {
                    'username': 'tester'
                },
                'useridentity': {
                    'sessioncontext': {
                        'sessionissuer': {
                            'username': 'InfosecAdmin'
                        }
                    }
                }
            }
        }
    }

    default_alert = {
        'category': 'privileges',
        'tags': ['aws', 'privileges'],
        'severity': 'NOTICE',
    }

    test_cases = [
        PositiveAlertTestCase(
            description='Fire when InfosecAdmin attaches policy',
            events=[default_event],
            expected_alert=default_alert),
        NegativeAlertTestCase(
            description='Does not fire if non-root user attaches policy',
            events=[non_root_user_evt]),
        NegativeAlertTestCase(
            description='Does not fire if action is not AttachUserPolicy',
            events=[not_attach_policy_evt])
    ]
