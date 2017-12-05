# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
# Copyright (c) 2017 Mozilla Corporation
#
# Contributors:
# Brandon Myers bmyers@mozilla.com

from positive_alert_test_case import PositiveAlertTestCase
from negative_alert_test_case import NegativeAlertTestCase

from alert_test_suite import AlertTestSuite


class TestAlertGeomodel(AlertTestSuite):
    default_event = {
        "_type": "event",
        "_source": {
            "category": "geomodelnotice",
            "summary": "ttesterson@mozilla.com NEWCOUNTRY Diamond Bar, United States access from 1.2.3.4 (duo) [deviation:12.07010770457331] last activity was from Ottawa, Canada (3763 km away) approx 23.43 hours before",
            "details": {
                "severity": 2,
                "category": "NEWCOUNTRY",
                "locality_details": {
                    "city": "Diamond Bar",
                    "country": "United States"
                },
                "principal": "ttesterson@mozilla.com",
                "source_ipv4": "1.2.3.4"
            }
        }
    }

    default_alert = {
        "category": "geomodel",
        "tags": ['geomodel'],
        "severity": "NOTICE",
        "notify_mozdefbot": False,
        "summary": "ttesterson@mozilla.com NEWCOUNTRY Diamond Bar, United States access from 1.2.3.4 (duo) [deviation:12.07010770457331] last activity was from Ottawa, Canada (3763 km away) approx 23.43 hours before",
        "details": {
            "category": "NEWCOUNTRY",
            "locality_details": {
                "city": "Diamond Bar",
                "country": "United States"
            },
            "principal": "ttesterson@mozilla.com",
            "source_ip": "1.2.3.4"
        }
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
    event['_source']['details']['severity'] = 3
    alert = AlertTestSuite.create_alert(default_alert)
    alert['notify_mozdefbot'] = True
    alert['severity'] = 'WARNING'
    test_cases.append(
        PositiveAlertTestCase(
            description="Positive test case with good event with high severity",
            events=[event],
            expected_alert=alert
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

    movement_event = {
        "_source": {
            u'category': u'geomodelnotice',
            u'details': {
                'category': 'MOVEMENT',
            },
            'severity': 'NOTICE',
            'source': 'UNKNOWN',
            'summary': 'person1@mozilla.com MOVEMENT window violation (London, United Kingdom) -> (San Jose, United States) -> (Frankfurt am Main, Germany) within 4h window',
        }
    }
    movement_alert = {
        "category": "geomodel",
        "tags": ['geomodel'],
        "severity": "NOTICE",
        "notify_mozdefbot": False,
        "summary": "person1@mozilla.com MOVEMENT window violation (London, United Kingdom) -> (San Jose, United States) -> (Frankfurt am Main, Germany) within 4h window",
    }
    test_cases.append(
        PositiveAlertTestCase(
            description="Positive test case with multiple localities",
            events=[AlertTestSuite.create_event(movement_event)],
            expected_alert=movement_alert
        )
    )

    event = AlertTestSuite.create_event(default_event)
    event['_source']['utctimestamp'] = AlertTestSuite.subtract_from_timestamp_lambda({'minutes': 31})
    event['_source']['receivedtimestamp'] = AlertTestSuite.subtract_from_timestamp_lambda({'minutes': 31})
    test_cases.append(
        NegativeAlertTestCase(
            description="Negative test case with an event with old timestamp",
            events=[event],
        )
    )

    event = AlertTestSuite.create_event(default_event)
    event['_type'] = 'badtype'
    test_cases.append(
        NegativeAlertTestCase(
            description="Negative test case with an event with bad type",
            events=[event],
        )
    )

    event = AlertTestSuite.create_event(default_event)
    event['_source']['category'] = 'badcategory'
    test_cases.append(
        NegativeAlertTestCase(
            description="Negative test case with an event with bad category",
            events=[event],
        )
    )

    event = AlertTestSuite.create_event(default_event)
    event['_source']['summary'] = 'user1@mozilla.com MOVEMENT window violation (London, United Kingdom) -> (San Jose, United States) -> (Frankfurt am Main, Germany) within 4h window'
    test_cases.append(
        NegativeAlertTestCase(
            description="Negative test case with an event with excluded username",
            events=[event],
        )
    )
