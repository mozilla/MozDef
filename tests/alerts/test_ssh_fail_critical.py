from positive_alert_test_case import PositiveAlertTestCase
from negative_alert_test_case import NegativeAlertTestCase

from alert_test_suite import AlertTestSuite


class TestSSHFailCrit(AlertTestSuite):
    alert_filename = "ssh_fail_critical"

    # This event is the default positive event that will cause the
    # alert to trigger
    default_event = {
        "_type": "event",
        "_source": {
            "category": "syslog",
            "summary": "Failed publickey for root from 1.2.3.4 port 48882 ssh2",
            "details": {
                "hostname": "random.server.com",
                "program": "sshd",
            }
        }
    }

    # This alert is the expected result from running this task
    default_alert = {
        "category": "session",
        "severity": "WARNING",
        "summary": "Failed to open session on example1.hostname.domain.com",
        "tags": ['pam', 'syslog'],
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
    event['_source']['utctimestamp'] = AlertTestSuite.subtract_from_timestamp_lambda({'minutes': 1})
    test_cases.append(
        PositiveAlertTestCase(
            description="Positive test case with an event with invalid user and IP",
            events=[
                {
                    "_source": {
                        "summary": "Invalid user batman from 1.2.3.4"
                    }
                }
            ],
            expected_alert=default_alert
        ),
        PositiveAlertTestCase(
            description="Positive test case with an event with just invalid user",
            events=[
                {
                    "_source": {
                        "summary": "input_userauth_request: invalid user robin"
                    }
                }
            ],
            expected_alert=default_alert
        ),
        PositiveAlertTestCase(
            description="Positive test case with an event with somewhat old timestamp",
            events=[event],
            expected_alert=default_alert
        )
    )

    event = AlertTestSuite.create_event(default_event)
    event['_type'] = "audit"
    test_cases.append(
        NegativeAlertTestCase(
            description="Negative test case with bad event type",
            events=[
                {
                    "_type": "audit",
                }
            ],
        )
    )

    event = AlertTestSuite.create_event(default_event)
    event['_source']['category'] = "badcategory"
    test_cases.append(
        NegativeAlertTestCase(
            description="Negative test case with bad eventName",
            events=[event],
        )
    )

    event = AlertTestSuite.create_event(default_event)
    event['_source']['summary'] = "Accepted publickey for root from 10.22.252.22 port 48882 ssh2"
    test_cases.append(
        NegativeAlertTestCase(
            description="Negative test case with bad summary",
            events=[event],
        )
    )

    event = AlertTestSuite.create_event(default_event)
    event['_source']['details']['hostname'] = "example2.hostname.domain.com"
    test_cases.append(
        NegativeAlertTestCase(
            description="Negative test case with bad details.hostname",
            events=[event],
        )
    )

    event = AlertTestSuite.create_event(default_event)
    event['_source']['utctimestamp'] = AlertTestSuite.subtract_from_timestamp_lambda({'minutes': 3})
    test_cases.append(
        NegativeAlertTestCase(
            description="Negative test case with old timestamp",
            events=[event],
        )
    )
