#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
# Copyright (c) 2017 Mozilla Corporation
#
# Contributors:
# Brandon Myers bmyers@mozilla.com


import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), "../lib"))
from elasticsearch_client import ElasticsearchClient

from utilities.toUTC import toUTC
from utilities.dot_dict import DotDict

from datetime import datetime, timedelta
from dateutil.parser import parse

from configlib import getConfig

from kombu import Connection, Queue, Exchange

import random
import pytest

import time

if not pytest.config.option.delete_indexes:
    warning_text = "\n\n** WARNING - Some unit tests will not pass unless the --delete_indexes is specified."
    warning_text += "\nThis is due to the fact that some tests need a 'clean' ES environment **\n"
    warning_text += "\n** DISCLAIMER - If you enable this flag, all indexes that MozDef uses will be deleted upon test execution **\n"
    print warning_text
else:
    warning_text = "\n\n** WARNING - The --delete_indexes flag has been set. We will be deleting important indexes from ES before test execution**\n"
    warning_text += "Continuing the unit test execution in 10 seconds...CANCEL ME IF YOU DO NOT WANT PREVIOUS INDEXES DELETED!!! **\n"
    print warning_text
    time.sleep(10)

if not pytest.config.option.delete_queues:
    warning_text = "\n\n** WARNING - Some unit tests will not pass unless the --delete_queues is specified."
    warning_text += "\nThis is due to the fact that some tests need a 'clean' RabbitMQ environment **\n"
    warning_text += "\n** DISCLAIMER - If you enable this flag, the queues in rabbitmq that MozDef uses will be deleted upon test execution **\n"
    print warning_text
else:
    warning_text = "\n** WARNING - The --delete_queues flag has been set. We will be purging RabbitMQ queues before test execution**\n"
    warning_text += "Continuing the unit test execution in 10 seconds...CANCEL ME IF YOU DO NOT WANT PREVIOUS QUEUES PURGED!!! **\n"
    print warning_text
    time.sleep(10)


class UnitTestSuite(object):

    def setup(self):
        current_date = datetime.now()
        self.event_index_name = current_date.strftime("events-%Y%m%d")
        self.previous_event_index_name = (current_date - timedelta(days=1)).strftime("events-%Y%m%d")
        self.alert_index_name = current_date.strftime("alerts-%Y%m")
        self.parse_config()

        # Elasticsearch
        self.es_client = ElasticsearchClient(list('{0}'.format(s) for s in self.options.esservers))

        # RabbitMQ
        mqConnString = 'amqp://{0}:{1}@{2}:{3}//'.format(self.options.mquser,
                                                        self.options.mqpassword,
                                                        self.options.mqalertserver,
                                                        self.options.mqport)

        mqAlertConn = Connection(mqConnString)
        alertExchange = Exchange(name=self.options.alertExchange, type='topic', durable=True, delivery_mode=1)
        alertExchange(mqAlertConn).declare()

        alertQueue = Queue(self.options.queueName,
                           exchange=alertExchange,
                           routing_key=self.options.alerttopic,
                           durable=False,
                           no_ack=(not self.options.mqack))
        alertQueue(mqAlertConn).declare()

        self.rabbitmq_alerts_consumer = mqAlertConn.Consumer(alertQueue, accept=['json'])

        if pytest.config.option.delete_indexes:
            self.reset_elasticsearch()
            self.setup_elasticsearch()

        if pytest.config.option.delete_queues:
            self.reset_rabbitmq()

    def parse_config(self):
        default_config = os.path.join(os.path.dirname(__file__), "config.conf")
        options = DotDict()
        options.configfile = default_config

        options.esservers = list(getConfig('esservers', 'http://localhost:9200', options.configfile).split(','))

        options.alertExchange = getConfig('alertexchange', 'alerts', options.configfile)
        options.queueName = getConfig('alertqueuename', 'alertBot', options.configfile)
        options.alerttopic = getConfig('alerttopic', 'mozdef.*', options.configfile)

        options.mquser = getConfig('mquser', 'guest', options.configfile)
        options.mqalertserver = getConfig('mqalertserver', 'localhost', options.configfile)
        options.mqpassword = getConfig('mqpassword', 'guest', options.configfile)
        options.mqport = getConfig('mqport', 5672, options.configfile)
        options.mqack = getConfig('mqack', True, options.configfile)

        self.options = options

    def reset_rabbitmq(self):
        self.rabbitmq_alerts_consumer.channel.queue_purge()

    def teardown(self):
        if pytest.config.option.delete_indexes:
            self.reset_elasticsearch()
        if pytest.config.option.delete_queues:
            self.reset_rabbitmq()

    def populate_test_event(self, event, event_type='event'):
        self.es_client.save_event(body=event, doc_type=event_type)

    def setup_elasticsearch(self):
        default_mapping_file = os.path.join(os.path.dirname(__file__), "../config/defaultMappingTemplate.json")
        mapping_str = ''
        with open(default_mapping_file) as data_file:
            mapping_str = data_file.read()

        self.es_client.create_index(self.event_index_name, mapping=mapping_str)
        self.es_client.create_alias('events', self.event_index_name)
        self.es_client.create_index(self.previous_event_index_name, mapping=mapping_str)
        self.es_client.create_alias('events-previous', self.previous_event_index_name)
        self.es_client.create_index(self.alert_index_name, mapping=mapping_str)
        self.es_client.create_alias('alerts', self.alert_index_name)

    def reset_elasticsearch(self):
        self.es_client.delete_index(self.event_index_name, True)
        self.es_client.delete_index('events', True)
        self.es_client.delete_index(self.previous_event_index_name, True)
        self.es_client.delete_index('events-previous', True)
        self.es_client.delete_index(self.alert_index_name, True)
        self.es_client.delete_index('alerts', True)

    def flush(self, index_name):
        self.es_client.flush(index_name)

    def random_ip(self):
        return str(random.randint(1, 255)) + "." + str(random.randint(1, 255)) + "." + str(random.randint(1, 255)) + "." + str(random.randint(1, 255))

    def generate_default_event(self):
        current_timestamp = UnitTestSuite.current_timestamp_lambda()

        source_ip = self.random_ip()

        event = {
            "_index": "events",
            "_type": "event",
            "_source": {
                "category": "excategory",
                "utctimestamp": current_timestamp,
                "receivedtimestamp": current_timestamp,
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
        for key, value in expected_event.iteritems():
            if key == 'receivedtimestamp':
                assert type(event[key]) == unicode
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
         notnow = toUTC(datetime.now().replace(hour=hour, minute=minute, second=second).isoformat())
         return notnow

    @staticmethod
    def current_timestamp_lambda():
        return lambda: UnitTestSuite.current_timestamp()

    @staticmethod
    def subtract_from_timestamp_lambda(date_timedelta, timestamp=None):
        return lambda: UnitTestSuite.subtract_from_timestamp(date_timedelta, timestamp)

    @staticmethod
    def create_timestamp_from_now_lambda(hour, minute, second):
        return lambda: UnitTestSuite.create_timestamp_from_now(hour, minute, second)
