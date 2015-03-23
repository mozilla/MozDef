#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
# Copyright (c) 2014 Mozilla Corporation
#
# Contributors:
# Jeff Bryner jbryner@mozilla.com
#
# Alert Worker to listen for alerts and call python plugins
# for user-controlled reaction to alerts.

import json
import kombu
import logging
import os
import pynsive
import sys
from configlib import getConfig, OptionParser
from kombu import Connection, Queue, Exchange
from kombu.mixins import ConsumerMixin
from logging.handlers import SysLogHandler
from operator import itemgetter

logger = logging.getLogger()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')


def registerPlugins():
    pluginList = list()   # tuple of module,registration dict,priority
    plugin_manager = pynsive.PluginManager()
    if os.path.exists('plugins'):
        modules = pynsive.list_modules('plugins')
        for mname in modules:
            module = pynsive.import_module(mname)
            reload(module)
            if not module:
                raise ImportError('Unable to load module {}'.format(mname))
            else:
                if 'message' in dir(module):
                    mclass = module.message()
                    mreg = mclass.registration
                    if 'priority' in dir(mclass):
                        mpriority = mclass.priority
                    else:
                        mpriority = 100
                    if isinstance(mreg, list):
                        print('[*] plugin {0} registered to receive messages with {1}'.format(mname, mreg))
                        pluginList.append((mclass, mreg, mpriority))
    return pluginList


def dict2List(inObj):
    '''given a dictionary, potentially with multiple sub dictionaries
       return a list of the dict keys and values
    '''
    if isinstance(inObj, dict):
        for key, value in inObj.iteritems():
            if isinstance(value, dict):
                for d in dict2List(value):
                    yield d
            elif isinstance(value, list):
                yield key.encode('ascii', 'ignore').lower()
                for l in dict2List(value):
                    yield l
            else:
                yield key.encode('ascii', 'ignore').lower()
                if isinstance(value, str):
                    yield value.lower()
                elif isinstance(value, unicode):
                    yield value.encode('ascii', 'ignore').lower()
                else:
                    yield value
    elif isinstance(inObj, list):
        for v in inObj:
            if isinstance(v, str):
                yield v.lower()
            elif isinstance(v, unicode):
                yield v.encode('ascii', 'ignore').lower()
            elif isinstance(v, list):
                for l in dict2List(v):
                    yield l
            elif isinstance(v, dict):
                for l in dict2List(v):
                    yield l                    
            else:
                yield v
    else:
        yield ''


def sendEventToPlugins(anevent, pluginList):
    '''compare the event to the plugin registrations.
       plugins register with a list of keys or values
       or values they want to match on
       this function compares that registration list
       to the current event and sends the event to plugins
       in order
    '''
    if not isinstance(anevent, dict):
        raise TypeError('event is type {0}, should be a dict'.format(type(anevent)))

    # expecting tuple of module,criteria,priority in pluginList
    # sort the plugin list by priority
    for plugin in sorted(pluginList, key=itemgetter(2), reverse=False):
        # assume we don't run this event through the plugin
        send = False
        if isinstance(plugin[1], list):
            try:
                if (set(plugin[1]).intersection([e for e in dict2List(anevent)])):
                    send = True
            except TypeError:
                sys.stderr.write('TypeError on set intersection for dict {0}'.format(anevent))
                return anevent
        if send:
            anevent = plugin[0].onMessage(anevent)

    return anevent


class alertConsumer(ConsumerMixin):
    '''read in alerts,
       compare them to plugins
       and send alerts to plugins as requested
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
            elif isinstance(body, str) or isinstance(body, unicode):
                try:
                    bodyDict = json.loads(body)  # lets assume it's json
                except ValueError as e:
                    # not json..ack but log the message
                    logger.exception(
                        "alertworker exception: unknown body type received %r" % body)
                    return
            else:
                logger.exception(
                    "alertworker exception: unknown body type received %r" % body)
                return
            # process valid message
            bodyDict = sendEventToPlugins(bodyDict, pluginList)

            message.ack()
        except ValueError as e:
            logger.exception(
                "alertworker exception while processing events queue %r" % e)


def main():
    sh = logging.StreamHandler(sys.stderr)
    sh.setFormatter(formatter)
    logger.addHandler(sh)

    # connect and declare the message queue/kombu objects.
    # Event server/exchange/queue
    mqConnString = 'amqp://{0}:{1}@{2}:{3}//'.format(options.mquser,
                                                        options.mqpassword,
                                                        options.mqalertserver,
                                                        options.mqport)
    mqAlertConn = Connection(mqConnString)

    # Exchange for alerts we pass to plugins
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
    pluginList = registerPlugins()
    main()
