#!/usr/bin/env python
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# Copyright (c) 2017 Mozilla Corporation
#
# Simple sample code to generate an event and deposit as json on rabbitmq

import optparse
import time

from datetime import datetime
from kombu import Connection, Exchange

from mozdef_util.utilities.toUTC import toUTC


parser = optparse.OptionParser()
parser.add_option('--rabbitmq_host', help='RabbitMQ host (default: localhost)', default='localhost')
parser.add_option('--rabbitmq_user', help='RabbitMQ username (default: guest)', default='guest')
parser.add_option('--rabbitmq_password', help='RabbitMQ password (default: guest)', default='guest')
parser.add_option('--rabbitmq_port', help='RabbitMQ port (default: 5672)', default=5672)
options, arguments = parser.parse_args()

events = [
    {
        "category": "testcategory",
        "details": {
            "program": "sshd",
            "type": "Success Login",
            "username": "ttesterson",
            "sourceipaddress": '1.2.3.4',
        },
        "processname": "auth0_cron",
        "severity": "INFO",
        "source": "auth0",
        "summary": "login invalid ldap_count_entries failed",
        "tags": ["auth0"],
        "timestamp": toUTC(datetime.now()).isoformat()
    }
]

# connect and declare the message queue/kombu objects.
# only py-amqp supports ssl and doesn't recognize amqps
# so fix up the connection string accordingly
# mqvhost is generally / by default, mqport is generally 5672
# sample with variables:
# connString = 'amqp://{0}:{1}@{2}:{3}/{4}'.format(mqusername, mqpassword, mqservername, mqport, mqvhost)

# sample with hard-coded values.
connString = 'amqp://{0}:{1}@{2}:{3}/{4}'.format(
    options.rabbitmq_user,
    options.rabbitmq_password,
    options.rabbitmq_host,
    options.rabbitmq_port,
    '/'
)

# ssl or not
mqConn = Connection(connString, ssl=False)

# Declare the Task Exchange for events
# delivery_mode=1 is fast/auto-ack messages, 2 is require ack.
# mozdef default exchange is: eventtask, routing key is also: eventtask
eventTaskExchange = Exchange(name='eventtask', type='direct', durable=True, delivery_mode=1)
eventTaskExchange(mqConn).declare()
mqproducer = mqConn.Producer(serializer='json')

# publish it to rabbit mq
ensurePublish = mqConn.ensure(mqproducer, mqproducer.publish, max_retries=10)
for event in events:
    ensurePublish(event, exchange=eventTaskExchange, routing_key='eventtask')
    print("Wrote event to rabbitmq")
    time.sleep(0.2)
