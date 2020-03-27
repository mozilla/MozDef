# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# Copyright (c) 2017 Mozilla Corporation

from .positive_alert_test_case import PositiveAlertTestCase
from .negative_alert_test_case import NegativeAlertTestCase

from .alert_test_suite import AlertTestSuite


class TestAlertDuoAuthFail(AlertTestSuite):
    alert_filename = "duo_authfail"

    # This event is the default positive event that will cause the
    # alert to trigger
    default_event = {
        "_source": {
            "category": "authentication",
            "summary": 'authentication FRAUD for you@somewhere.com',
            "details": {
                "sourceipaddress": "1.2.3.4",
                "username": "you@somewhere.com",
                "result": "fraud",
            }
        }
    }

    # This alert is the expected result from running this task
    default_alert = {
        "category": "duosecurity",
        "tags": ['duosecurity', 'duosecurity_auth_fail'],
        "severity": "WARNING",
        "url": "https://www.mozilla.org",
        "summary": "Duo Authentication Failure: user you@somewhere.com rejected and marked a Duo Authentication attempt from 1.2.3.4 as fraud",
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
            description="Negative test case with bad category",
            events=[event],
        )
    )

    event = AlertTestSuite.create_event(default_event)
    event['_source']['details']['result'] = 'SUCCESS'
    test_cases.append(
        NegativeAlertTestCase(
            description="Negative test case with bad result",
            events=[event],
        )
    )

    event = AlertTestSuite.create_event(default_event)
    event['_source']['details']['sourceipaddress'] = None
    test_cases.append(
        NegativeAlertTestCase(
            description="Negative test case without the details.sourceipaddress",
            events=[event],
        )
    )

    event = AlertTestSuite.create_event(default_event)
    event['_source']['details']['username'] = None
    test_cases.append(
        NegativeAlertTestCase(
            description="Negative test case without the details.username",
            events=[event],
        )
    )

    event = AlertTestSuite.create_event(default_event)
    event['_source']['utctimestamp'] = AlertTestSuite.subtract_from_timestamp_lambda({'minutes': 16})
    event['_source']['receivedtimestamp'] = AlertTestSuite.subtract_from_timestamp_lambda({'minutes': 16})
    test_cases.append(
        NegativeAlertTestCase(
            description="Negative test case with a wrong timestamp",
            events=[event],
        )
    )
