#!/usr/bin/env python
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# Copyright (c) 2014 Mozilla Corporation

"""mozdef bot using KitnIRC."""
import json
import kitnirc.client
import kitnirc.modular
import logging
import netaddr
import os
import random
import sys
import time
from configlib import getConfig, OptionParser
from datetime import datetime
from kombu import Connection, Queue, Exchange
from kombu.mixins import ConsumerMixin
from ipwhois import IPWhois

from mozdef_util.utilities.toUTC import toUTC
from mozdef_util.geo_ip import GeoIP


logger = logging.getLogger()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

greetz = ["mozdef bot in da house",
          "mozdef here..what's up",
          "mozdef has joined the room..no one panic",
          "mozdef bot here..nice to see everyone"]

panics = ["don't panic",
          ".. a towel has immense psychological value",
          "..but in fact the message was this: 'So Long, and Thanks for All the Fish.'",
          "42",
          "What I need..is a strong drink and a peer group --Douglas Adams",
          "Eddies in the space-time continuum.",
          "segmentation fault..SEP"
          ]

if os.path.isfile('quotes.txt'):
    quotes = open('quotes.txt').readlines()
else:
    quotes = ['nothing to say..add a quotes.txt file!']

colors = {'red': '\x034\x02',
          'normal': '\x03\x02',
          'blue': '\x032\x02',
          'green': '\x033\x02',
          'yellow': '\x038\x02',
          }

keywords = {'INFORMATIONAL': colors['green'],
            'INFO': colors['green'],
            'WARNING': colors['yellow'],
            'CRITICAL': colors['red'],
            }


def colorify(data):
    for i in keywords:
        data = data.replace(i, keywords[i] + i + colors['normal'], 1)
    return data


def run_async(func):
    """
    run_async(func)
    function decorator, intended to make "func" run in a separate
    thread (asynchronously).
    Returns the created Thread object
    from: http://code.activestate.com/recipes/576684-simple-threading-decorator/

    E.g.:
    @run_async
    def task1():
    do_something

    @run_async
    def task2():
    do_something_too

    t1 = task1()
    t2 = task2()
    ...
    t1.join()
    t2.join()
    """
    from threading import Thread
    from functools import wraps

    @wraps(func)
    def async_func(*args, **kwargs):
        func_hl = Thread(target=func, args=args, kwargs=kwargs)
        func_hl.start()
        return func_hl
    return async_func


def getQuote():
    aquote = '{0} --Mos Def'.format(
        quotes[random.randint(0, len(quotes) - 1)].strip())
    return aquote


def isIP(ip):
    try:
        netaddr.IPNetwork(ip)
        return True
    except:
        return False


def ipLocation(ip):
    location = ""
    try:
        geoip_data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../data/GeoLite2-City.mmdb")
        geoip = GeoIP(geoip_data_dir)
        geoDict = geoip.lookup_ip(ip)
        if geoDict is not None:
            if 'error' in geoDict:
                return geoDict['error']
            location = geoDict['country_name']
            if geoDict['country_code'] in ('US'):
                if geoDict['metro_code']:
                    location = location + '/{0}'.format(geoDict['metro_code'])
    except Exception:
        location = ""
    return location


def formatAlert(jsonDictIn):
    # defaults
    severity = 'INFO'
    summary = ''
    category = ''
    if 'severity' in jsonDictIn:
        severity = jsonDictIn['severity']
    if 'summary' in jsonDictIn:
        summary = jsonDictIn['summary']
    if 'category' in jsonDictIn:
        category = jsonDictIn['category']

    return colorify('{0}: {1} {2}'.format(
        severity,
        colors['blue'] + category + colors['normal'],
        summary
    ))


class mozdefBot():

    def __init__(self, ):
        # Logging initialization
        self.log_handler = logging.StreamHandler()
        self.log_formatter = logging.Formatter("%(asctime)s %(message)s")
        self.log_handler.setFormatter(self.log_formatter)

        self.root_logger = logging.getLogger()
        self.root_logger.addHandler(self.log_handler)
        self.root_logger.setLevel(logging.INFO)

        self.client = kitnirc.client.Client(options.host, options.port)
        self.controller = kitnirc.modular.Controller(self.client, options.configfile)
        self.controller.load_config()
        self.controller.start()
        self.client.root_logger = self.root_logger
        self.client.connect(
            nick=options.nick,
            username=options.username or options.nick,
            realname=options.realname or options.username or options.nick,
            password=options.password,
            ssl=True
        )
        self.mqConsumer = None

    def run(self):
        try:
            @self.client.handle('WELCOME')
            def join_channels(client, *params):
                if not options.join:
                    return
                for chan in options.join.split(","):
                    if chan in options.channelkeys:
                        client.join(chan, options.channelkeys[chan])
                    else:
                        client.join(chan)
                # start the mq consumer
                consumeAlerts(self)

            @self.client.handle('PRIVMSG')
            def priv_handler(client, actor, recipient, message):
                self.root_logger.debug(
                    'privmsggot:' + message + ' from ' + actor)

                if "!help" in message:
                    self.client.msg(
                        recipient, "Help on it's way...try these:")
                    self.client.msg(
                        recipient, "!quote  --get a quote from my buddy Mos Def")
                    self.client.msg(recipient, "!panic  --panic (or not )")
                    self.client.msg(
                        recipient, "!ipinfo --do a geoip lookup on an ip address")
                    self.client.msg(
                        recipient, "!ipwhois --do a whois lookup on an ip address")

                if "!quote" in message:
                    self.client.msg(recipient, getQuote())

                if "!panic" in message:
                    self.client.msg(recipient, random.choice(panics))

                if '!ipwhois' in message:
                    for field in message.split():
                        if isIP(field):
                            ip = netaddr.IPNetwork(field)[0]
                            if (not ip.is_loopback() and not ip.is_private() and not ip.is_reserved()):
                                whois = IPWhois(ip).lookup_whois()
                                description = whois['nets'][0]['description']
                                self.client.msg(
                                    recipient, "{0} description: {1}".format(field, description))
                            else:
                                self.client.msg(
                                    recipient, "{0}: hrm..loopback? private ip?".format(field))

                if "!ipinfo" in message:
                    for i in message.split():
                        if isIP(i):
                            ip = netaddr.IPNetwork(i)[0]
                            if (not ip.is_loopback() and not ip.is_private() and not ip.is_reserved()):
                                self.client.msg(
                                    recipient, "{0} location: {1}".format(i, ipLocation(i)))
                            else:
                                self.client.msg(
                                    recipient, "{0}: hrm..loopback? private ip?".format(i))

            @self.client.handle('JOIN')
            def join_handler(client, user, channel, *params):
                self.root_logger.debug('%r' % channel)
                if user.nick == options.nick:
                    self.client.msg(channel, colorify(random.choice(greetz)))
            self.client.run()

        except KeyboardInterrupt:
            self.client.disconnect()
            if self.mqConsumer:
                try:
                    self.mqConsumer.should_stop = True
                except:
                    pass

        except Exception as e:
            sys.stdout.write('stdout - bot error, quitting {0}'.format(e))
            self.client.root_logger.error('bot error..quitting {0}'.format(e))
            self.client.disconnect()
            if self.mqConsumer:
                try:
                    self.mqConsumer.should_stop = True
                except:
                    pass


class alertConsumer(ConsumerMixin):
    '''read in alerts and hand back to the
       kitnirc class for publishing
    '''

    def __init__(self, mqAlertsConnection, alertQueue, alertExchange, ircBot):
        self.connection = mqAlertsConnection  # default connection for the kombu mixin
        self.alertsConnection = mqAlertsConnection
        self.alertQueue = alertQueue
        self.alertExchange = alertExchange
        self.ircBot = ircBot
        self.lastalert = None
        ircBot.mqConsumer = self

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
                full_body = body
            elif isinstance(body, str):
                try:
                    full_body = json.loads(body)  # lets assume it's json
                except ValueError:
                    # not json..ack but log the message
                    logger.exception(
                        "alertworker exception: unknown body type received %r" % body)
                    return
            else:
                logger.exception(
                    "alertworker exception: unknown body type received %r" % body)
                return

            body_dict = full_body
            # Handle messages that have full ES dict
            if '_source' in full_body:
                body_dict = full_body['_source']

            if 'notify_mozdefbot' in body_dict and body_dict['notify_mozdefbot'] is False:
                # If the alert tells us to not notify, then don't post to IRC
                message.ack()
                return

            # process valid message
            # see where we send this alert
            channel = options.alertchannel
            if 'channel' in body_dict:
                if body_dict['channel'] in options.join.split(","):
                    channel = body_dict['channel']

            # see if we need to delay a bit before sending the alert, to avoid
            # flooding the channel
            if self.lastalert is not None:
                delta = toUTC(datetime.now()) - self.lastalert
                sys.stdout.write('new alert, delta since last is {}\n'.format(delta))
                if delta.seconds < 2:
                    sys.stdout.write('throttling before writing next alert\n')
                    time.sleep(1)
            self.lastalert = toUTC(datetime.now())
            if len(body_dict['summary']) > 450:
                sys.stdout.write('alert is more than 450 bytes, truncating\n')
                body_dict['summary'] = body_dict['summary'][:450] + ' truncated...'

            self.ircBot.client.msg(channel, formatAlert(body_dict))

            message.ack()
        except ValueError as e:
            logger.exception(
                "alertworker exception while processing events queue %r" % e)


@run_async
def consumeAlerts(ircBot):
    # connect and declare the message queue/kombu objects.
    # server/exchange/queue
    mqConnString = 'amqp://{0}:{1}@{2}:{3}//'.format(
        options.mquser,
        options.mqpassword,
        options.mqalertserver,
        options.mqport
    )
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
    alertConsumer(mqAlertConn, alertQueue, alertExchange, ircBot).run()


def initConfig():
    # initialize config options
    # sets defaults or overrides from config file.

    # irc options
    options.host = getConfig('host', 'irc.somewhere.com', options.configfile)
    options.nick = getConfig('nick', 'mozdefnick', options.configfile)
    options.port = getConfig('port', 6697, options.configfile)
    options.username = getConfig('username', 'username', options.configfile)
    options.realname = getConfig('realname', 'realname', options.configfile)
    options.password = getConfig('password', '', options.configfile)

    # Our config parser removes '#'
    # so we gotta re-add them
    options.join = getConfig('join', '#mzdf', options.configfile)
    channels = []
    for channel in options.join.split(','):
        if not channel.startswith('#'):
            channel = '#{0}'.format(channel)
        channels.append(channel)
    options.join = ','.join(channels)

    options.alertchannel = getConfig(
        'alertchannel',
        '',
        options.configfile)

    options.channelkeys = json.loads(getConfig(
        'channelkeys',
        '{"#somechannel": "somekey"}',
        options.configfile))

    # Our config parser stomps out the '#' so we gotta readd
    channelkeys = {}
    for key, value in options.channelkeys.items():
        if not key.startswith('#'):
            key = '#{0}'.format(key)
        channelkeys[key] = value
    options.channelkeys = channelkeys

    # message queue options
    # server hostname
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
        'alertBot',
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

    if options.alertchannel == '':
        options.alertchannel = options.join.split(",")[0]


if __name__ == "__main__":
    sh = logging.StreamHandler(sys.stderr)
    sh.setFormatter(formatter)
    logger.addHandler(sh)

    parser = OptionParser()
    parser.add_option(
        "-c", dest='configfile',
        default=sys.argv[0].replace('.py', '.conf'),
        help="configuration file to use")
    (options, args) = parser.parse_args()
    initConfig()

    # run the IRC class
    # which in turn starts the mq consumer
    theBot = mozdefBot()
    theBot.run()

# vim: set ts=4 sts=4 sw=4 et:
