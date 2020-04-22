# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# Copyright (c) 2017 Mozilla Corporation
from .positive_alert_test_case import PositiveAlertTestCase
from .negative_alert_test_case import NegativeAlertTestCase
from .alert_test_suite import AlertTestSuite


class TestldapAdd(AlertTestSuite):
    alert_filename = "ldap_add"
    # This event is the default positive event that will cause the
    # alert to trigger
    default_event = {
        "_source": {
            "summary": "dc=example mail=user_la@example.com,o=com,dc=example IP=1.2.3.4:49818 conn=527493 add cn=example_cn,ou=groups,dc=example",
            "details": {
                "dn": "cn=example_cn,ou=groups,dc=example",
                "changetype": "add",
                "actor": "dc=example mail=user_la@example.com,o=com,dc=example IP=1.2.3.4:49818 conn=527493"
            },
            "category": "ldapChange",
            "processid": "1697",
            "severity": "INFO",
        }
    }

    # This alert is the expected result from running this task
    default_alert = {
        "category": "ldap",
        "tags": ["ldap"],
        "severity": "INFO",
        "summary": "dc=example mail=user_la@example.com,o=com,dc=example IP=1.2.3.4:49818 conn=527493 added cn=example_cn,ou=groups,dc=example",
    }

    test_cases = []

    test_cases.append(
        PositiveAlertTestCase(
            description="Positive test case with good event",
            events=[AlertTestSuite.create_event(default_event)],
            expected_alert=default_alert
        )
    )

    event = AlertTestSuite.create_event(default_event)
    event['_source']['utctimestamp'] = AlertTestSuite.subtract_from_timestamp_lambda({'minutes': 1})
    event['_source']['receivedtimestamp'] = AlertTestSuite.subtract_from_timestamp_lambda({'minutes': 1})
    test_cases.append(
        PositiveAlertTestCase(
            description="Positive test case with an event with somewhat old timestamp",
            events=[event],
            expected_alert=default_alert
        )
    )

    event = AlertTestSuite.create_event(default_event)
    event['_source']['category'] = 'badcategory'
    test_cases.append(
        NegativeAlertTestCase(
            description="Negative test case with bad eventName",
            events=[event],
        )
    )

    event = AlertTestSuite.create_event(default_event)
    event['_source']['details']['changetype'] = 'delete'
    test_cases.append(
        NegativeAlertTestCase(
            description="Negative test case with bad changetype",
            events=[event],
        )
    )

    event = AlertTestSuite.create_event(default_event)
    event['_source']['details']['actor'] = 'dc=example uid=bind-generate-groups,ou=logins,dc=example IP=1.2.3.4:49818 conn=527493'
    test_cases.append(
        NegativeAlertTestCase(
            description="Negative test case where negative match exists",
            events=[event],
        )
    )

    event = AlertTestSuite.create_event(default_event)
    event['_source']['utctimestamp'] = AlertTestSuite.subtract_from_timestamp_lambda({'hours': 25})
    event['_source']['receivedtimestamp'] = AlertTestSuite.subtract_from_timestamp_lambda({'hours': 25})
    test_cases.append(
        NegativeAlertTestCase(
            description="Negative test case with event with old utctimestamp and receivedtimestamp",
            events=[event],
        )
    )
