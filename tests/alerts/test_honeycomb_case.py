# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# Copyright (c) 2017 Mozilla Corporation

from .positive_alert_test_case import PositiveAlertTestCase
from .negative_alert_test_case import NegativeAlertTestCase

from .alert_test_suite import AlertTestSuite


class TestAlertHoneycomb(AlertTestSuite):
    alert_filename = "honeycomb"

    # This event is the default positive event that will cause the
    # alert to trigger
    default_event = {
        "_source": {
            "category": "syslog",
            "severity": "CRIT",
            "processname": "Honeycomb",
            "hostname": "foo.bar.com",
            "summary": ('id="1a6c32ec-e900-464b-b517-da8845a9e735"'
                        ' status="2" timestamp="2018-09-20 13:10:3'
                        '7.889056" event_type="simple_http" event_'
                        'description="HTTP Server Interaction" req'
                        'uest="GET /" originating_ip="1.2.3.4'
                        '" originating_port="60104" decoy_os="Linu'
                        'x" __weakref__="None"')
        }
    }

    # This alert is the expected result from running this task
    default_alert = {
        "category": "honeypot",
        "tags": ['honeypot', 'honeycomb'],
        "severity": "WARNING",
        "summary": 'Honeypot activity on foo.bar.com from IP(s): 1.2.3.4',
    }

    test_cases = []

    test_cases.append(
        PositiveAlertTestCase(
            description="Positive test with default events and default alert expected",
            events=AlertTestSuite.create_events(default_event, 10),
            expected_alert=default_alert
        )
    )

    # Generating another event to simulate multiple hostile source IPs
    default_event2 = AlertTestSuite.copy(default_event)
    default_event2['_source']['summary'] = ('id="1a6c32ec-e900-464b-b517-da8845a9e735"'
                                            ' status="2" timestamp="2018-09-20 13:10:3'
                                            '7.889056" event_type="simple_http" event_'
                                            'description="HTTP Server Interaction" req'
                                            'uest="GET /" originating_ip="1.2.3.5'
                                            '" originating_port="60104" decoy_os="Linu'
                                            'x" __weakref__="None"')

    # This alert is the expected result from running this task
    default_multi_ip_alert = AlertTestSuite.copy(default_alert)
    default_multi_ip_alert['summary'] = 'Honeypot activity on foo.bar.com from IP(s): 1.2.3.4, 1.2.3.5'

    events1 = AlertTestSuite.create_events(default_event, 5)
    events2 = AlertTestSuite.create_events(default_event2, 5)
    test_cases.append(
        PositiveAlertTestCase(
            description="Positive test with events with multiple IPs and default alert with a multi-IP summary",
            events=events1 + events2,
            expected_alert=default_multi_ip_alert
        )
    )

    events = AlertTestSuite.create_events(default_event, 10)
    for event in events:
        event['_source']['category'] = 'bad category example'
    test_cases.append(
        NegativeAlertTestCase(
            description="Negative test case with events with incorrect category",
            events=events,
        )
    )

    events = AlertTestSuite.create_events(default_event, 10)
    for event in events:
        event['_source']['severity'] = 'bad severity example'
    test_cases.append(
        NegativeAlertTestCase(
            description="Negative test case with events with incorrect severity",
            events=events,
        )
    )

    events = AlertTestSuite.create_events(default_event, 10)
    for event in events:
        event['_source']['processname'] = 'bad processname example'
    test_cases.append(
        NegativeAlertTestCase(
            description="Negative test case with events with incorrect processname",
            events=events,
        )
    )

    events = AlertTestSuite.create_events(default_event, 10)
    for event in events:
        event['_source']['utctimestamp'] = AlertTestSuite.subtract_from_timestamp_lambda({
            'minutes': 241})
        event['_source']['receivedtimestamp'] = AlertTestSuite.subtract_from_timestamp_lambda({
            'minutes': 241})
    test_cases.append(
        NegativeAlertTestCase(
            description="Negative test case with old timestamp",
            events=events,
        )
    )
