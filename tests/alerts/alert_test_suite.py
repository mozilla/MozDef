#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# Copyright (c) 2017 Mozilla Corporation

import os.path
import sys
import logging

from tests.unit_test_suite import UnitTestSuite

from freezegun import freeze_time
import mock

import copy
import re
import json


def mock_add_hostname_to_ip(ip):
    if ip == '10.2.3.4':
        return ['mock_hostname1.mozilla.org', ip]
    else:
        return ['mock.mozilla.org', ip]


class AlertTestSuite(UnitTestSuite):
    def teardown(self):
        os.chdir(self.orig_path)
        super().teardown()
        sys.path.remove(self.alerts_path)
        sys.path.remove(self.alerts_lib_path)
        if 'lib' in sys.modules:
            del sys.modules['lib']

    def setup(self):
        self.orig_path = os.getcwd()
        super().setup()
        self.alerts_path = os.path.join(os.path.dirname(__file__), "../../alerts")
        self.alerts_lib_path = os.path.join(os.path.dirname(__file__), "../../alerts/lib")
        sys.path.insert(0, self.alerts_path)
        sys.path.insert(0, self.alerts_lib_path)
        from lib import alerttask

        # Overwrite the ES and RABBITMQ configs for alerts
        # since it pulls it from alerts/lib/config.py
        alerttask.ES = {
            'servers': list('{0}'.format(s) for s in self.options.esservers)
        }
        alerttask.RABBITMQ = {
            'mquser': self.options.mquser,
            'alertexchange': self.options.alertExchange,
            'alertqueue': self.options.alertqueue,
            'mqport': self.options.mqport,
            'mqserver': self.options.mqserver,
            'mqpassword': self.options.mqpassword,
            'mqalertserver': self.options.mqalertserver
        }

        alerts_dir = os.path.join(os.path.dirname(__file__), "../../alerts/")
        os.chdir(alerts_dir)

        if not hasattr(self, 'alert_classname'):
            self.alert_classname = (self.__class__.__name__[4:] if
                                    self.__class__.__name__.startswith('Test') else
                                    False)

        if not hasattr(self, 'alert_filename'):
            # Convert "AlertFooBar" to "foo_bar" and "BazQux" to "baz_qux"
            self.alert_filename = re.sub(
                '([a-z0-9])([A-Z])',
                r'\1_\2',
                re.sub(
                    '(.)([A-Z][a-z]+)',
                    r'\1_\2',
                    self.alert_classname[5:] if
                    self.alert_classname.startswith('Alert') else
                    self.alert_classname)).lower()

        # Boolean to determine if an alert is a 'deadman' type of alert
        # Meaning, this will throw if no events are found
        if not hasattr(self, 'deadman'):
            self.deadman = False

        # Log to stdout so pytest will report any
        # stack traces on any test failures
        logging.basicConfig(stream=sys.stdout, level=logging.ERROR)

    # Some housekeeping stuff here to make sure the data we get is 'good'
    def verify_starting_values(self, test_case):
        # Verify the description for the test case is populated
        assert test_case.description is not None or ""
        assert test_case.description is not ""

        # Verify alert_filename is a legit file
        full_alert_file_path = "./" + self.alert_filename + ".py"
        assert os.path.isfile(full_alert_file_path) is True

        # Verify we're able to load in the alert_classname
        # This can probably be improved, but for the mean time, we're just
        # gonna grep for class name
        alert_source_str = open(full_alert_file_path, 'r').read()
        class_search_str = "class " + self.alert_classname + "("
        error_text = "Incorrect alert classname. We tried guessing the class name ({0}), but that wasn't it.".format(self.alert_classname)
        error_text += ' Define self.alert_classname in your alert unit test class.'
        assert class_search_str in alert_source_str, error_text

        # Verify events is not empty
        assert len(test_case.events) is not 0

        # Verify that if we're a positive test case, we actually passed in an
        # expected_alert
        if test_case.expected_test_result is True:
            assert test_case.expected_alert is not None
        else:
            # How can we expect an alert, when we're expecting the alert to
            # never throw?
            assert test_case.expected_alert is None

    # todo: remote this out to utilities
    def dict_merge(self, target, *args):
        # Merge multiple dicts
        if len(args) > 1:
            for obj in args:
                self.dict_merge(target, obj)
            return target

        # Recursively merge dicts and set non-dict values
        obj = args[0]
        if not isinstance(obj, dict):
            return obj
        for k, v in obj.items():
            if k in target and isinstance(target[k], dict):
                self.dict_merge(target[k], v)
            else:
                target[k] = v
        return target

    @freeze_time("2017-01-01 01:00:00", tz_offset=0)
    def test_alert_test_case(self, test_case):
        self.verify_starting_values(test_case)
        temp_events = test_case.events
        for event in temp_events:
            temp_event = self.dict_merge(self.generate_default_event(), self.default_event)

            merged_event = self.dict_merge(temp_event, event)
            merged_event['_source']['utctimestamp'] = merged_event['_source']['utctimestamp']()
            merged_event['_source']['receivedtimestamp'] = merged_event['_source']['receivedtimestamp']()
            test_case.full_events.append(merged_event)
            self.populate_test_event(merged_event['_source'])

        self.refresh('events')

        with mock.patch("socket.gethostbyaddr", side_effect=mock_add_hostname_to_ip):
            alert_task = test_case.run(alert_filename=self.alert_filename, alert_classname=self.alert_classname)
        self.verify_alert_task(alert_task, test_case)

    def verify_rabbitmq_alert(self, found_alert, test_case):
        rabbitmq_message = self.rabbitmq_alerts_consumer.channel.basic_get()
        rabbitmq_message.channel.basic_ack(rabbitmq_message.delivery_tag)
        document = json.loads(rabbitmq_message.body)
        assert '_id' in document
        assert '_source' in document
        assert '_index' in document
        alert_body = document['_source']
        assert alert_body['notify_mozdefbot'] is test_case.expected_alert['notify_mozdefbot'], 'Alert from rabbitmq has bad notify_mozdefbot field'
        assert alert_body['channel'] == test_case.expected_alert['channel'], 'Alert from rabbitmq has bad channel field'
        assert alert_body['summary'] == found_alert['_source']['summary'], 'Alert from rabbitmq has bad summary field'
        assert alert_body['utctimestamp'] == found_alert['_source']['utctimestamp'], 'Alert from rabbitmq has bad utctimestamp field'
        assert alert_body['category'] == found_alert['_source']['category'], 'Alert from rabbitmq has bad category field'
        assert len(alert_body['events']) == len(found_alert['_source']['events']), 'Alert from rabbitmq has bad events field'

    def verify_saved_events(self, found_alert, test_case):
        """
        Verifies the events saved in ES has expected values from an alert running
        """
        # Deadman alerts throw when no events are found, so skip
        # any of the event validation
        if self.deadman:
            return

        # If we override the number of expected events, let's use that value
        num_events = len(test_case.full_events)
        if hasattr(self, 'num_samples'):
            num_events = self.num_samples
        assert len(found_alert['_source']['events']) == num_events

        for event in found_alert['_source']['events']:
            event_id = event['documentid']
            found_event = self.es_client.get_event_by_id(event_id)
            assert found_event['_source']['alert_names'] == [self.alert_classname]
            assert len(found_event['_source']['alerts']) > 0
            for alert in found_event['_source']['alerts']:
                assert alert['id'] == found_alert['_id']
                assert alert['index'] == found_alert['_index']

    def verify_expected_alert(self, found_alert, test_case):
        # Verify index is set correctly
        assert found_alert['_index'] == self.alert_index_name, 'Alert index not propertly set, got: {}'.format(found_alert['_index'])

        # Verify that the alert has the right "look to it"
        assert sorted(found_alert.keys()) == ['_id', '_index', '_score', '_source'], 'Alert format is malformed'

        # Verify the alert has an id field that is str
        assert type(found_alert['_id']) == str, 'Alert _id is malformed'

        # Verify there is a utctimestamp field
        assert 'utctimestamp' in found_alert['_source'], 'Alert does not have utctimestamp specified'

        if 'channel' not in test_case.expected_alert:
            test_case.expected_alert['channel'] = None

        # Verify notify_mozdefbot is set correctly based on severity
        expected_notify_mozdefbot = True
        if (test_case.expected_alert['severity'] == 'NOTICE' or test_case.expected_alert['severity'] == 'INFO') and test_case.expected_alert['channel'] is None:
            expected_notify_mozdefbot = False
        test_case.expected_alert['notify_mozdefbot'] = expected_notify_mozdefbot

        # Verify channel is set correctly
        assert found_alert['_source']['channel'] == test_case.expected_alert['channel'], 'Alert channel field is bad'

        # Verify classname is set correctly
        assert found_alert['_source']['classname'] == self.alert_classname, 'Alert classname field is bad'

        # Verify the events are added onto the alert
        assert type(found_alert['_source']['events']) == list, 'Alert events field is not a list'

        # Verify that the alert properties are set correctly
        for key, value in test_case.expected_alert.items():
            assert found_alert['_source'][key] == value, '{0} does not match!\n\tgot: {1}\n\texpected: {2}'.format(key, found_alert['_source'][key], value)

    def verify_alert_task(self, alert_task, test_case):
        assert alert_task.classname() == self.alert_classname, 'Alert classname did not match expected name'
        if test_case.expected_test_result is True:
            assert len(alert_task.alert_ids) is not 0, 'Alert did not fire as expected'
            self.refresh('alerts')
            self.refresh('events')
            for alert_id in alert_task.alert_ids:
                found_alert = self.es_client.get_alert_by_id(alert_id)
                self.verify_expected_alert(found_alert, test_case)
                self.verify_saved_events(found_alert, test_case)
                self.verify_rabbitmq_alert(found_alert, test_case)
        else:
            assert len(alert_task.alert_ids) is 0, 'Alert fired when it was expected not to'

    @staticmethod
    def copy(obj):
        return copy.deepcopy(obj)

    @staticmethod
    def create_events(default_event, num_events):
        events = []
        for num in range(num_events):
            events.append(AlertTestSuite.create_event(default_event))
        return events

    @staticmethod
    def create_event(default_event):
        return copy.deepcopy(default_event)

    @staticmethod
    def create_alert(default_alert):
        return AlertTestSuite.create_event(default_alert)
