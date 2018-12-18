#!/usr/bin/env python
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
# Copyright (c) 2014 Mozilla Corporation

""" mozdef bot using slack
    to install - 'pip install slackclient'
"""

import json
import random
import sys
import os
import time
import netaddr
from ipwhois import IPWhois
from configlib import getConfig, OptionParser
from datetime import datetime
from kombu import Connection, Queue, Exchange
from kombu.mixins import ConsumerMixin

from slackclient import SlackClient

from mozdef_util.utilities.toUTC import toUTC
from mozdef_util.geo_ip import GeoIP
from mozdef_util.utilities.logger import logger


greetings = [
    "mozdef bot in da house",
    "mozdef here..what's up",
    "mozdef has joined the room..no one panic",
    "mozdef bot here..nice to see everyone"
]


def isIP(ip):
    try:
        netaddr.IPNetwork(ip)
        return True
    except Exception:
        return False


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
    summary = jsonDictIn['summary']
    if 'category' in jsonDictIn.keys():
        summary = "_{0}_: {1}".format(jsonDictIn['category'], summary)
    return summary


def handle_ipinfo(ip_token):
    if isIP(ip_token):
        ip = netaddr.IPNetwork(ip_token)[0]
        if (not ip.is_loopback() and not ip.is_private() and not ip.is_reserved()):
            response = "{0} location: {1}".format(ip_token, ipLocation(ip_token))
        else:
            response = "{0}: hrm...loopback? private ip?".format(ip_token)
    else:
        response = "{0} is not an IP address".format(ip_token)
    return response


def handle_ipwhois(ip_token):
    if isIP(ip_token):
        ip = netaddr.IPNetwork(ip_token)[0]
        if (not ip.is_loopback() and not ip.is_private() and not ip.is_reserved()):
            whois = IPWhois(ip).lookup_whois()
            description = str(whois['nets'][0]['description']).encode('string_escape')
            response = "{0} description: {1}".format(ip_token, description)
        else:
            response = "{0}: hrm...loopback? private ip?".format(ip_token)
    else:
        response = "{0} is not an IP address".format(ip_token)
    return response


class SlackBot(object):
    def __init__(self, api_key, channels, bot_name):
        self.slack_client = SlackClient(api_key)
        self.channels = channels
        self.bot_name = bot_name
        self.bot_id = self.get_bot_id()

    def run(self):
        if self.slack_client.rtm_connect():
            logger.info("Bot connected to slack")
            self.post_welcome_message(random.choice(greetings))
            consumeAlerts(self)
            self.listen_for_messages()
        else:
            logger.error("Unable to connect to slack")
            sys.exit(1)

    def handle_command(self, message_text):
        response = ""
        message_tokens = message_text.split()
        command = message_tokens[0]
        parameters = message_tokens[1:len(message_tokens)]
        if command == '!help':
            response = """
Help on it's way...try these:

!ipinfo --do a geoip lookup on an ip address
!ipwhois --do a whois lookup on an ip address
            """
        elif command == '!ipinfo':
            for ip_token in parameters:
                response += "\n" + handle_ipinfo(ip_token)
        elif command == '!ipwhois':
            for ip_token in parameters:
                response += "\n" + handle_ipwhois(ip_token)
        else:
            response = "Unknown command: " + command + ". Try !help"

        return response

    def parse_command(self, content):
        # messages look like this:
        # pwnbus: @mozdef !help
        tokens = content.split('@' + self.bot_name)
        command = tokens[1].strip()
        return command

    def handle_message(self, message):
        channel = message['channel']
        thread_ts = message['ts']
        # If we're already in a thread, reply within that thread
        if 'thread_ts' in message:
            thread_ts = message['thread_ts']
        content = message['content']
        command = self.parse_command(content)

        response = self.handle_command(command)
        if response is not "":
            self.post_thread_message(
                text=response,
                channel=channel,
                thread_ts=thread_ts
            )

    def listen_for_messages(self):
        while True:
            for slack_message in self.slack_client.rtm_read():
                message_type = slack_message.get('type')
                if message_type == 'desktop_notification':
                    self.handle_message(slack_message)
            time.sleep(1)

    def post_thread_message(self, text, channel, thread_ts):
        self.slack_client.api_call(
            "chat.postMessage",
            as_user="true",
            channel=channel,
            text=text,
            thread_ts=thread_ts
        )

    def post_attachment(self, message, channel, color):
        if channel is None:
            message_channels = self.channels
        else:
            message_channels = [channel]

        for message_channel in message_channels:
            attachment = {
                'fallback': message,
                'text': message,
                'color': color
            }
            self.slack_client.api_call("chat.postMessage", channel=message_channel, attachments=[attachment], as_user=True)

    def post_welcome_message(self, message, channel=None):
        self.post_attachment(message, channel, '#36a64f')

    def post_info_message(self, message, channel=None):
        self.post_attachment(message, channel, '#99ccff')

    def post_critical_message(self, message, channel=None):
        self.post_attachment(message, channel, '#ff0000')

    def post_warning_message(self, message, channel=None):
        self.post_attachment(message, channel, '#e6e600')

    def post_notice_message(self, message, channel=None):
        self.post_attachment(message, channel, '#a64dff')

    def post_unknown_severity_message(self, message, channel=None):
        self.post_attachment(message, channel, '#000000')

    def get_bot_id(self):
        api_call = self.slack_client.api_call("users.list")
        if api_call.get('ok'):
            # retrieve all users so we can find our bot
            users = api_call.get('members')
            for user in users:
                if 'name' in user and user.get('name') == self.bot_name:
                    return user.get('id')


class alertConsumer(ConsumerMixin):

    def __init__(self, mqAlertsConnection, alertQueue, alertExchange, bot):
        self.connection = mqAlertsConnection  # default connection for the kombu mixin
        self.alertsConnection = mqAlertsConnection
        self.alertQueue = alertQueue
        self.alertExchange = alertExchange
        self.bot = bot
        self.lastalert = None
        self.bot.mqConsumer = self

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
                    logger.exception("mozdefbot_slack exception: unknown body type received %r" % body)
                    return
            else:
                logger.exception("mozdefbot_slack exception: unknown body type received %r" % body)
                return

            if 'notify_mozdefbot' in bodyDict and bodyDict['notify_mozdefbot'] is False:
                # If the alert tells us to not notify, then don't post message
                message.ack()
                return

            # process valid message
            # see where we send this alert
            channel = options.default_alert_channel
            if 'ircchannel' in bodyDict.keys():
                if bodyDict['ircchannel'] in options.channels:
                    channel = bodyDict['ircchannel']

            # see if we need to delay a bit before sending the alert, to avoid
            # flooding the channel
            if self.lastalert is not None:
                delta = toUTC(datetime.now()) - self.lastalert
                sys.stdout.write('new alert, delta since last is {}\n'.format(delta))
                if delta.seconds < 2:
                    sys.stdout.write('throttling before writing next alert\n')
                    time.sleep(1)
            self.lastalert = toUTC(datetime.now())
            if len(bodyDict['summary']) > 450:
                sys.stdout.write('alert is more than 450 bytes, truncating\n')
                bodyDict['summary'] = bodyDict['summary'][:450] + ' truncated...'

            severity = bodyDict['severity'].upper()
            if severity == 'CRITICAL':
                self.bot.post_critical_message(formatAlert(bodyDict), channel)
            elif severity == 'WARNING':
                self.bot.post_warning_message(formatAlert(bodyDict), channel)
            elif severity == 'INFO':
                self.bot.post_info_message(formatAlert(bodyDict), channel)
            elif severity == 'NOTICE':
                self.bot.post_notice_message(formatAlert(bodyDict), channel)
            else:
                self.bot.post_unknown_severity_message(formatAlert(bodyDict), channel)
            message.ack()
        except ValueError as e:
            logger.exception("mozdefbot_slack exception while processing events queue %r" % e)


@run_async
def consumeAlerts(bot):
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
    alertConsumer(mqAlertConn, alertQueue, alertExchange, bot).run()


def initConfig():
    options.slack_token = getConfig('slack_token', '<CHANGE ME>', options.configfile)
    options.name = getConfig('name', 'mozdef', options.configfile)
    options.channels = getConfig('channels', 'general', options.configfile).split(',')
    options.default_alert_channel = getConfig('default_alert_channel', 'mozdef', options.configfile)

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
    options.mqalertserver = getConfig('mqalertserver', 'localhost', options.configfile)
    options.mquser = getConfig('mquser', 'guest', options.configfile)
    options.mqpassword = getConfig('mqpassword', 'guest', options.configfile)
    options.mqport = getConfig('mqport', 5672, options.configfile)
    # mqack=True sets persistant delivery, False sets transient delivery
    options.mqack = getConfig('mqack', True, options.configfile)


if __name__ == "__main__":
    parser = OptionParser()
    parser.add_option(
        "-c", dest='configfile',
        default=sys.argv[0].replace('.py', '.conf'),
        help="configuration file to use")
    (options, args) = parser.parse_args()
    initConfig()

    theBot = SlackBot(options.slack_token, options.channels, options.name)
    theBot.run()
