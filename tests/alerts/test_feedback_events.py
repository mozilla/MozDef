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


class TestAlertFeedbackEvents(AlertTestSuite):
    default_event = {
        "_type": "event",
        "_source": {
            "category": "user_feedback",
            "tags": [
                "sso-mozdef-feedback-events"
            ],
            "details": {
                "action": "escalate",
                "alert_information": {
                    "category": "geomodel",
                    "severity": "NOTICE",
                    "utctimestamp": "2017-12-07T14:54:08.092467+00:00",
                    "tags": [
                        "geomodel"
                    ],
                    "notify_mozdefbot": False,
                    "ircchannel": None,
                    "summary": "ttesterson@mozilla.com NEWCOUNTRY Unknown, United States access from 1.2.3.4 (auth0) [deviation:0.5] last activity was from Berlin, Germany (8182 km away) approx 503.93 hours before",
                    "details": {
                        "category": "NEWCOUNTRY",
                        "source_ip": "1.2.3.4",
                        "locality_details": {
                            "city": "Unknown",
                            "country": "United States"
                        },
                        "principal": "ttesterson@mozilla.com"
                    },
                    "events": [
                        {
                            "documentindex": "events-20171207",
                            "documentsource": {
                                "category": "geomodelnotice",
                                "processid": "563",
                                "mozdefhostname": "mozdefhost",
                                "severity": "NOTICE",
                                "utctimestamp": "2017-12-07T14:54:08.092467+00:00",
                                "tags": [
                                    "geomodel"
                                ],
                                "timestamp": "2017-12-07T14:54:08.092467+00:00",
                                "hostname": "hostmozdef",
                                "receivedtimestamp": "2017-12-07T14:54:08.092467+00:00",
                                "summary": "ttesterson@mozilla.com NEWCOUNTRY Unknown, United States access from 1.2.3.4 (auth0) [deviation:0.5] last activity was from Berlin, Germany (8182 km away) approx 503.93 hours before",
                                "processname": "/home/geomodel/go/bin/geomodel",
                                "details": {
                                    "category": "NEWCOUNTRY",
                                    "prev_distance": 8182.322788482041,
                                    "prev_locality_details": {
                                        "city": "Berlin",
                                        "country": "Germany"
                                    },
                                    "prev_timestamp": "2017-11-14T14:47:13Z",
                                    "severity": 2,
                                    "event_time": "2017-12-07T14:42:54.466Z",
                                    "longitude": -97.822,
                                    "prev_latitude": 48.179,
                                    "source_ipv4": "1.2.3.4",
                                    "latitude": 37.751,
                                    "locality_details": {
                                        "city": "Unknown",
                                        "country": "United States"
                                    },
                                    "informer": "auth0",
                                    "prev_longitude": 11.2547,
                                    "weight_deviation": 0.5,
                                    "principal": "ttesterson@mozilla.com"
                                }
                            },
                            "documentid": "AWAnKtprWc8M_JNGim7Q",
                            "documenttype": "event"
                        }
                    ]
                }
            }
        }
    }

    default_alert = {
        "category": "geomodel",
        "tags": ['feedback', 'customtag1'],
        "severity": "NOTICE",
        "notify_mozdefbot": False,
        "summary": "SSO Escalate Event Received",
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
    default_event['_source']['details']['alert_information']['category'] = 'othercategory'
    alert = AlertTestSuite.create_alert(default_alert)
    alert['tags'] = ['feedback', 'customtag2']
    test_cases.append(
        PositiveAlertTestCase(
            description="Positive test case with good event",
            events=[AlertTestSuite.create_event(default_event)],
            expected_alert=alert
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
    event['_source']['details']['action'] = 'badaction'
    test_cases.append(
        NegativeAlertTestCase(
            description="Negative test case with an event with bad action",
            events=[event],
        )
    )
