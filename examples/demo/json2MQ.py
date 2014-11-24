#!/usr/bin/env python
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
# Copyright (c) 2014 Mozilla Corporation
#
# Contributors:
# Jeff Bryner jbryner@mozilla.com
#
# Simple sample code to generate an event and deposit as json on rabbitmq
#

import json
import kombu
import os
import pyes
import pytz
import sys
import time
from datetime import datetime
from kombu import Connection, Queue, Exchange


# connect and declare the message queue/kombu objects.
# only py-amqp supports ssl and doesn't recognize amqps
# so fix up the connection string accordingly
# mqvhost is generally / by default, mqport is generally 5672
# sample with variables:
#connString = 'amqp://{0}:{1}@{2}:{3}/{4}'.format(mqusername, mqpassword, mqservername, mqport, mqvhost)

# sample with hard-coded values.
connString = 'amqp://{0}:{1}@{2}:{3}/{4}'.format('guest', 'guest', 'servername', 5672, '/')

#ssl or not
mqConn = Connection(connString, ssl=False)

# Declare the Task Exchange for events
# delivery_mode=1 is fast/auto-ack messages, 2 is require ack.
# mozdef default exchange is: eventtask, routing key is also: eventtask
eventTaskExchange = Exchange(name='eventtask', type='direct', durable=True, delivery_mode=1)
eventTaskExchange(mqConn).declare()
mqproducer = mqConn.Producer(serializer='json')

# make an event
event = dict()
# best practice is to send an ISO formatted timestamp
# so upstream can tell the source time zone
event['timestamp'] = pytz.timezone('UTC').localize(datetime.utcnow()).isoformat()
event['summary'] = 'just a test, only a test'
event['category'] = 'testing'
event['severity'] = 'INFO'
event['processid']=os.getpid()
event['processname']=sys.argv[0]
event['tags'] = list()
event['tags'].append('test')
event['details'] = dict()
event['details']['sourceipaddress'] = '1.2.3.4'


# publish it to rabbit mq

ensurePublish=mqConn.ensure(mqproducer,mqproducer.publish,max_retries=10)
ensurePublish(event,exchange=eventTaskExchange,routing_key='eventtask')