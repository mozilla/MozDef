#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# Copyright (c) 2017 Mozilla Corporation

from datetime import datetime, timedelta
from dateutil.parser import parse

import random
import sys

from mozdef_util.utilities import toUTC

from tests.suite_helper import parse_config_file, parse_mapping_file, setup_es_client, setup_rabbitmq_client


class UnitTestSuite(object):
    config_delete_indexes = None
    config_delete_queues = None

    def setup(self):
        self.options = parse_config_file()
        self.mapping_options = parse_mapping_file()
        self.es_client = setup_es_client(self.options)
        self.rabbitmq_alerts_consumer = setup_rabbitmq_client(self.options)

        current_date = datetime.now()
        self.event_index_name = current_date.strftime("events-%Y%m%d")
        self.previous_event_index_name = (current_date - timedelta(days=1)).strftime("events-%Y%m%d")
        self.alert_index_name = current_date.strftime("alerts-%Y%m")

        if self.config_delete_indexes:
            self.reset_elasticsearch()
            self.setup_elasticsearch()

        if self.config_delete_queues:
            self.reset_rabbitmq()

    def reset_rabbitmq(self):
        self.rabbitmq_alerts_consumer.channel.queue_purge()

    def teardown(self):
        if self.config_delete_indexes:
            self.reset_elasticsearch()
        if self.config_delete_queues:
            self.reset_rabbitmq()
        # Remove any leftover plugin module as a result of loading
        if 'plugins' in sys.modules:
            del sys.modules['plugins']

    def populate_test_event(self, event):
        self.es_client.save_event(body=event)

    def populate_test_object(self, event):
        self.es_client.save_object(index='events', body=event)

    def setup_elasticsearch(self):
        self.es_client.create_index(self.event_index_name, index_config=self.mapping_options)
        self.es_client.create_alias('events', self.event_index_name)
        self.es_client.create_index(self.previous_event_index_name, index_config=self.mapping_options)
        self.es_client.create_alias('events-previous', self.previous_event_index_name)
        self.es_client.create_alias_multiple_indices('events-weekly', [self.event_index_name, self.previous_event_index_name])
        self.es_client.create_index(self.alert_index_name, index_config=self.mapping_options)
        self.es_client.create_alias('alerts', self.alert_index_name)

    def reset_elasticsearch(self):
        self.es_client.delete_index(self.event_index_name, True)
        self.es_client.delete_index('events', True)
        self.es_client.delete_index(self.previous_event_index_name, True)
        self.es_client.delete_index('events-previous', True)
        self.es_client.delete_index(self.alert_index_name, True)
        self.es_client.delete_index('alerts', True)

    def refresh(self, index_name):
        self.es_client.refresh(index_name)

    def random_ip(self):
        return str(random.randint(1, 255)) + "." + str(random.randint(1, 255)) + "." + str(random.randint(1, 255)) + "." + str(random.randint(1, 255))

    def generate_default_event(self):
        current_timestamp = UnitTestSuite.current_timestamp_lambda()

        source_ip = self.random_ip()

        event = {
            "_index": "events",
            "_source": {
                "category": "excategory",
                "utctimestamp": current_timestamp,
                "receivedtimestamp": current_timestamp,
                "mozdefhostname": "mozdefhost",
                "hostname": "exhostname",
                "severity": "NOTICE",
                "source": "exsource",
                "summary": "Example summary",
                "tags": ['tag1', 'tag2'],
                "details": {
                    "sourceipaddress": source_ip,
                    "hostname": "exhostname"
                }
            }
        }

        return event

    def verify_event(self, event, expected_event):
        assert sorted(event.keys()) == sorted(expected_event.keys())
        for key, value in expected_event.items():
            if key in ('receivedtimestamp', 'timestamp', 'utctimestamp'):
                assert type(event[key]) == str
            else:
                assert event[key] == value, 'Incorrect match for {0}, expected: {1}'.format(key, value)

    @staticmethod
    def current_timestamp():
        return toUTC(datetime.now()).isoformat()

    @staticmethod
    def subtract_from_timestamp(date_timedelta, timestamp=None):
        if timestamp is None:
            timestamp = UnitTestSuite.current_timestamp()
        utc_time = parse(timestamp)
        custom_date = utc_time - timedelta(**date_timedelta)
        return custom_date.isoformat()

    @staticmethod
    def create_timestamp_from_now(hour, minute, second):
        return toUTC(datetime.now().replace(hour=hour, minute=minute, second=second).isoformat())

    @staticmethod
    def current_timestamp_lambda():
        return lambda: UnitTestSuite.current_timestamp()

    @staticmethod
    def subtract_from_timestamp_lambda(date_timedelta, timestamp=None):
        return lambda: UnitTestSuite.subtract_from_timestamp(date_timedelta, timestamp)

    @staticmethod
    def create_timestamp_from_now_lambda(hour, minute, second):
        return lambda: UnitTestSuite.create_timestamp_from_now(hour, minute, second)
