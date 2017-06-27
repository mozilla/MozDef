#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
# Copyright (c) 2017 Mozilla Corporation
#
# Contributors:
# bmyers@mozilla.com

from positive_alert_test_case import PositiveAlertTestCase
from negative_alert_test_case import NegativeAlertTestCase

from alert_test_suite import AlertTestSuite


class TestAlertUnauthScan(AlertTestSuite):
    alert_filename = "unauth_scan"
    alert_classname = "AlertUnauthInternalScan"

    # This event is the default positive event that will cause the
    # alert to trigger
    default_event = {
        "_type": "bro",
        "_source": {
            "category": "bronotice",
            "summary": "Scan::Port_Scan 1.2.3.4 scanned at least 12 unique ports of host 5.6.7.8 in 0m3s local",
            "eventsource": "nsm",
            "hostname": "nsmservername",
            "details": {
                "uid": "",
                "actions": "Notice::ACTION_LOG",
                "note": "Scan::Address_Scan",
                "sourceipv4address": "0.0.0.0",
                "indicators": [
                    "1.2.3.4"
                ],
                "p": '22',
                "msg": "1.2.3.4 scanned at least 12 unique ports of host 5.6.7.8 in 0m3s",
                "destinationipaddress": "5.6.7.8",
            },
        }
    }

    # This alert is the expected result from running this task
    default_alert = {
        'category': 'scan',
        'severity': 'NOTICE',
        'summary': "nsmservername: Unauthorized Internal Scan Event from [u'1.2.3.4'] scanning ports 22",
        'tags': [],
        'url': 'https://www.mozilla.org',
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
    test_cases.append(
        PositiveAlertTestCase(
            description="Positive test case with an event with somewhat old timestamp",
            events=[event],
            expected_alert=default_alert
        )
    )

    event = AlertTestSuite.create_event(default_event)
    event['_type'] = 'event'
    test_cases.append(
        NegativeAlertTestCase(
            description="Negative test case with bad event type",
            events=[event],
        )
    )

    event = AlertTestSuite.create_event(default_event)
    event['_source']['category'] = 'Badcategory'
    test_cases.append(
        NegativeAlertTestCase(
            description="Negative test case with bad category",
            events=[event],
        )
    )

    event = AlertTestSuite.create_event(default_event)
    event['_source']['eventsource'] = 'Badeventsource'
    test_cases.append(
        NegativeAlertTestCase(
            description="Negative test case with bad eventsource",
            events=[event],
        )
    )

    event = AlertTestSuite.create_event(default_event)
    event['_source']['details']['indicators'] = None
    test_cases.append(
        NegativeAlertTestCase(
            description="Negative test case with non existent details.indicators",
            events=[event],
        )
    )

    event = AlertTestSuite.create_event(default_event)
    event['_source']['details']['note'] = 'Badnote'
    test_cases.append(
        NegativeAlertTestCase(
            description="Negative test case with bad details.note",
            events=[event],
        )
    )

    event = AlertTestSuite.create_event(default_event)
    event['_source']['utctimestamp'] = AlertTestSuite.subtract_from_timestamp_lambda({'minutes': 31})
    test_cases.append(
        NegativeAlertTestCase(
            description="Negative test case with old timestamp",
            events=[event],
        )
    )
