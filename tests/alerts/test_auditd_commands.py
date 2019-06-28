from .positive_alert_test_case import PositiveAlertTestCase
from .negative_alert_test_case import NegativeAlertTestCase

from .alert_test_suite import AlertTestSuite


class TestAlertAuditdCommands(AlertTestSuite):
    alert_filename = "auditd_commands"

    # This event is the default positive event that will cause the
    # alert to trigger
    default_event = {
        "_source": {
            "category": "auditd",
            "hostname": "host1.mozilla.com",
            "details": {
                "processname": 'command1',
                "originaluser": "ttesterson"
            }
        }
    }

    # This alert is the expected result from running this task
    default_alert = {
        "category": "auditd",
        "severity": "WARNING",
        "summary": "ttesterson on host1.mozilla.com executed command1",
        "tags": ['auditd_command'],
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
    event['_source']['category'] = "execve"
    test_cases.append(
        PositiveAlertTestCase(
            description="Positive test case with execve as the category",
            events=[event],
            expected_alert=default_alert
        )
    )

    event = AlertTestSuite.create_event(default_event)
    event['_source']['details']['processname'] = 'command2'
    alert = AlertTestSuite.create_alert(default_alert)
    alert['summary'] = "ttesterson on host1.mozilla.com executed command2"
    test_cases.append(
        PositiveAlertTestCase(
            description="Positive test case with additional command",
            events=[event],
            expected_alert=alert
        )
    )

    event = AlertTestSuite.create_event(default_event)
    event['_source']['utctimestamp'] = AlertTestSuite.subtract_from_timestamp_lambda({'minutes': 29})
    event['_source']['receivedtimestamp'] = AlertTestSuite.subtract_from_timestamp_lambda({'minutes': 29})
    test_cases.append(
        PositiveAlertTestCase(
            description="Positive test case with event that's somewhat old",
            events=[event],
            expected_alert=default_alert
        )
    )

    event = AlertTestSuite.create_event(default_event)
    event['_source']['details']['processname'] = 'ls'
    test_cases.append(
        NegativeAlertTestCase(
            description="Negative test case with bad processname",
            events=[event],
        )
    )

    event = AlertTestSuite.create_event(default_event)
    event['_source']['category'] = "someother"
    event['_source']['tags'] = ["othervalue"]
    test_cases.append(
        NegativeAlertTestCase(
            description="Negative test case with bad tags and category",
            events=[event],
        )
    )

    event = AlertTestSuite.create_event(default_event)
    event['_source']['utctimestamp'] = AlertTestSuite.subtract_from_timestamp_lambda({'minutes': 31})
    event['_source']['receivedtimestamp'] = AlertTestSuite.subtract_from_timestamp_lambda({'minutes': 31})
    test_cases.append(
        NegativeAlertTestCase(
            description="Negative test case with an old event",
            events=[event],
        )
    )
