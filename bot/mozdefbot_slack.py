#!/usr/bin/env python
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
# Copyright (c) 2014 Mozilla Corporation

""" mozdef bot using slack
    to install - 'pip install slackclient'
"""

import json
import logging
import random
import sys
import time
from configlib import getConfig, OptionParser
from datetime import datetime
from kombu import Connection, Queue, Exchange
from kombu.mixins import ConsumerMixin

from slackclient import SlackClient

import sys
import os
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../lib'))
from utilities.toUTC import toUTC



logger = logging.getLogger()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

greetz = ["mozdef bot in da house",
          "mozdef here..what's up",
          "mozdef has joined the room..no one panic",
          "mozdef bot here..nice to see everyone"]


def formatAlert(jsonDictIn):
    # defaults
    summary = ''
    if 'summary' in jsonDictIn.keys():
        summary = jsonDictIn['summary']
    return summary


class SlackBot(object):
    def __init__(self, api_key, channels, bot_name):
        self.slack_client = SlackClient(api_key)
        self.channels = channels
        self.bot_name = bot_name
        self.bot_id = self.get_bot_id()

    def run(self):
        if self.slack_client.rtm_connect():
            print("SlackBot connected and running!")
            self.post_welcome_message(random.choice(greetz))
        else:
            print("Unable to connect")

    def handle_command(self, command, channel):
        print(command)

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

    def parse_slack_output(self, slack_rtm_output):
        output_list = slack_rtm_output
        if output_list and len(output_list) > 0:
            for output in output_list:
                AT_BOT = "<@" + self.bot_id + ">"
                if output and 'text' in output and AT_BOT in output['text']:
                    # return text after the @ mention, whitespace removed
                    return output['text'].split(AT_BOT)[1].strip().lower(), output['channel']
        return None, None

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
        bot.mqConsumer = self

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
            channel = options.alert_channel
            if 'channel' in bodyDict.keys():
                if bodyDict['channel'] in options.channels:
                    channel = bodyDict['channel']

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

def consumeAlerts(bot):
    # connect and declare the message queue/kombu objects.
    # server/exchange/queue
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
    alertConsumer(mqAlertConn, alertQueue, alertExchange, bot).run()


def initConfig():
    options.slack_token = getConfig('slack_token', '<CHANGE ME>', options.configfile)
    options.name = getConfig('name', 'mozdef', options.configfile)
    options.channels = getConfig('channels', 'general', options.configfile).split(',')
    options.alert_channel = getConfig('alert_channel', 'siem', options.configfile)

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

    theBot = SlackBot(options.slack_token, options.channels, options.name)
    theBot.run()
    consumeAlerts(theBot)
