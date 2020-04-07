from tests.alerts.alert_test_suite import AlertTestSuite
from tests.alerts.negative_alert_test_case import NegativeAlertTestCase
from tests.alerts.positive_alert_test_case import PositiveAlertTestCase


class TestAlertSensitiveUserUID0(AlertTestSuite):
    alert_filename = 'sensitiveuser_uid0'

    default_event = {
        '_source': {
            'hostname': 'example',
            'details': {
                'uid': 0,
                'user': 'sensitive'
            }
        }
    }

    expect_no_trigger_evt = {
        '_source': {
            'hostname': 'example',
            'details': {
                'uid': 1024,
                'user': 'sensitive'
            }
        }
    }

    expect_alert = {
        'category': 'anomaly',
        'tags': ['uid0', 'anomaly'],
        'severity': 'CRITICAL',
        'summary': 'User sensitive with uid 0 active on host example'
    }

    test_cases = [
        PositiveAlertTestCase(
            description='Only triggers when uid == 0',
            events=[default_event],
            expected_alert=expect_alert),
        NegativeAlertTestCase(
            description='Do not trigger when uid != 0',
            events=[expect_no_trigger_evt])
    ]
