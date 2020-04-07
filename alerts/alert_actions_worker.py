#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# Copyright (c) 2014 Mozilla Corporation
#
# Alert Worker to listen for alerts and call python actions
# for a user-controlled reaction to alerts.
# This worker receives a copy of an alert.

import json
import os
import sys
from configlib import getConfig, OptionParser
from kombu import Connection, Queue, Exchange
from kombu.mixins import ConsumerMixin

from lib.alert_plugin_set import AlertPluginSet
from lib.config import ALERT_ACTIONS

from mozdef_util.utilities.logger import logger, initLogger


class alertConsumer(ConsumerMixin):
    '''read in alerts,
       compare them to actions
       and send alerts to actions as requested
       '''

    def __init__(self, mqAlertsConnection, alertQueue, alertExchange):
        self.connection = mqAlertsConnection  # default connection for the kombu mixin
        self.alertsConnection = mqAlertsConnection
        self.alertQueue = alertQueue
        self.alertExchange = alertExchange

    def get_consumers(self, Consumer, channel):
        consumer = Consumer(
            self.alertQueue,
            callbacks=[self.on_message],
            accept=['json'])
        consumer.qos(prefetch_count=options.prefetch)
        return [consumer]

    def on_message(self, body, message):
        try:
            # just to be safe..check what we were sent.
            if isinstance(body, dict):
                bodyDict = body
            elif isinstance(body, str):
                try:
                    bodyDict = json.loads(body)  # lets assume it's json
                except ValueError as e:
                    # not json..ack but log the message
                    logger.exception("alertworker exception: unknown body type received %r" % body)
                    return
            else:
                logger.exception("alertworker exception: unknown body type received %r" % body)
                return
            # process valid message
            bodyDict = action_set.run_plugins(bodyDict)

            message.ack()
        except ValueError as e:
            logger.exception("alertworker exception while processing events queue %r" % e)


def main():
    # connect and declare the message queue/kombu objects.
    # Event server/exchange/queue
    mqConnString = 'amqp://{0}:{1}@{2}:{3}//'.format(
        options.mquser,
        options.mqpassword,
        options.mqalertserver,
        options.mqport
    )
    mqAlertConn = Connection(mqConnString)

    # Exchange for alerts we pass to actions
    alertExchange = Exchange(name=options.alertExchange,
                             type='topic',
                             durable=True,
                             delivery_mode=1)

    alertExchange(mqAlertConn).declare()

    # Queue for the exchange
    alertQueue = Queue(options.queueName,
                       exchange=alertExchange,
                       routing_key=options.alerttopic,
                       durable=False,
                       no_ack=(not options.mqack))
    alertQueue(mqAlertConn).declare()

    # consume our alerts.
    alertConsumer(mqAlertConn, alertQueue, alertExchange).run()


def initConfig():
    '''setup the default options and override with any in our .conf file'''

    # message queue server hostname
    options.mqalertserver = getConfig(
        'mqalertserver',
        'localhost',
        options.configfile)

    # queue exchange name
    options.alertExchange = getConfig(
        'alertexchange',
        'alerts',
        options.configfile)

    # queue name
    options.queueName = getConfig(
        'alertqueuename',
        'alertPlugins',
        options.configfile)

    # queue topic
    options.alerttopic = getConfig(
        'alerttopic',
        'mozdef.*',
        options.configfile)

    # how many messages to ask for at once
    options.prefetch = getConfig('prefetch', 50, options.configfile)
    options.mquser = getConfig('mquser', 'guest', options.configfile)
    options.mqpassword = getConfig('mqpassword', 'guest', options.configfile)
    options.mqport = getConfig('mqport', 5672, options.configfile)
    # mqack=True sets persistant delivery, False sets transient delivery
    options.mqack = getConfig('mqack', True, options.configfile)


if __name__ == '__main__':
    parser = OptionParser()
    parser.add_option("-c",
                      dest='configfile',
                      default=sys.argv[0].replace('.py', '.conf'),
                      help="configuration file to use")
    (options, args) = parser.parse_args()
    initConfig()
    initLogger(options)
    action_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), 'actions'))
    action_set = AlertPluginSet(action_dir, ALERT_ACTIONS)

    main()
