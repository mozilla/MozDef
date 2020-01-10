#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# Copyright (c) 2017 Mozilla Corporation

from configlib import getConfig

from kombu import Connection, Queue, Exchange

import os

from mozdef_util.elasticsearch_client import ElasticsearchClient
from mozdef_util.utilities.dot_dict import DotDict


# The following functions before the UnitTest class definition
# are a poor man's way to setup resourcing and ensure
# that we only setup a client on time per test suite run
# todo: Fix this by defining an init method when we switch
# from pytest to UnitTest
def parse_config_file():
    global CONFIG_FILE_CONTENTS
    try:
        CONFIG_FILE_CONTENTS
    except NameError:
        default_config = os.path.join(os.path.dirname(__file__), "config.conf")
        options = DotDict()
        options.configfile = default_config

        options.esservers = list(getConfig('esservers', 'http://localhost:9200', options.configfile).split(','))

        options.alertExchange = getConfig('alertexchange', 'alerts', options.configfile)
        options.queueName = getConfig('alertqueuename', 'alertBot', options.configfile)
        options.alertqueue = getConfig('alertqueue', 'mozdef.alert', options.configfile)
        options.alerttopic = getConfig('alerttopic', 'mozdef.*', options.configfile)

        options.mquser = getConfig('mquser', 'guest', options.configfile)
        options.mqalertserver = getConfig('mqalertserver', 'localhost', options.configfile)
        options.mqserver = getConfig('mqserver', 'localhost', options.configfile)
        options.mqpassword = getConfig('mqpassword', 'guest', options.configfile)
        options.mqport = getConfig('mqport', 5672, options.configfile)
        options.mqack = getConfig('mqack', True, options.configfile)

        options.mongohost = getConfig('mongohost', 'localhost', options.configfile)
        options.mongoport = getConfig('mongoport', 3002, options.configfile)

        CONFIG_FILE_CONTENTS = options

    return CONFIG_FILE_CONTENTS


def parse_mapping_file():
    global MAPPING_FILE_CONTENTS
    try:
        MAPPING_FILE_CONTENTS
    except NameError:
        default_mapping_file = os.path.join(os.path.dirname(__file__), "../cron/defaultMappingTemplate.json")
        with open(default_mapping_file) as data_file:
            MAPPING_FILE_CONTENTS = data_file.read()
    return MAPPING_FILE_CONTENTS


def setup_es_client(options):
    global ES_CLIENT
    try:
        ES_CLIENT
    except NameError:
        ES_CLIENT = ElasticsearchClient(list('{0}'.format(s) for s in options.esservers))
    return ES_CLIENT


def setup_rabbitmq_client(options):
    global RABBITMQ_CLIENT
    try:
        RABBITMQ_CLIENT
    except NameError:
        mqConnString = 'amqp://{0}:{1}@{2}:{3}//'.format(
            options.mquser,
            options.mqpassword,
            options.mqalertserver,
            options.mqport
        )
        mqAlertConn = Connection(mqConnString)
        alertExchange = Exchange(name=options.alertExchange, type='topic', durable=True, delivery_mode=1)
        alertExchange(mqAlertConn).declare()

        alertQueue = Queue(options.queueName,
                           exchange=alertExchange,
                           routing_key=options.alerttopic,
                           durable=False,
                           no_ack=(not options.mqack))
        alertQueue(mqAlertConn).declare()

        RABBITMQ_CLIENT = mqAlertConn.Consumer(alertQueue, accept=['json'])
    return RABBITMQ_CLIENT
