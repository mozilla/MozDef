#!/usr/bin/env python
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# Copyright (c) 2014 Mozilla Corporation

""" mozdef bot using slack
    to install - 'pip install slackclient'
"""

import json
import sys
import time
from configlib import OptionParser
from configlib import getConfig as get_config
from datetime import datetime
from kombu import Connection, Queue, Exchange
from kombu.mixins import ConsumerMixin
from threading import Thread


from mozdef_util.utilities.toUTC import toUTC
from mozdef_util.utilities.logger import logger

from slack_bot import SlackBot


class AlertConsumer(ConsumerMixin):

    def __init__(self, mq_alerts_connection, alert_queue, alert_exchange, bot):
        self.connection = mq_alerts_connection  # default connection for the kombu mixin
        self.alertsConnection = mq_alerts_connection
        self.alert_queue = alert_queue
        self.alert_exchange = alert_exchange
        self.bot = bot
        self.lastalert = None
        self.bot.mq_consumer = self

    def get_consumers(self, Consumer, channel):
        consumer = Consumer(
            self.alert_queue,
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
                    full_body = json.loads(body)
                except ValueError:
                    # not json..ack but log the message
                    logger.exception("mozdefbot_slack exception: unknown body type received %r" % body)
                    return
            else:
                logger.exception("mozdefbot_slack exception: unknown body type received %r" % body)
                return

            body_dict = full_body
            # Handle messages that have full ES dict
            if '_source' in full_body:
                body_dict = full_body['_source']

            if 'notify_mozdefbot' in body_dict and body_dict['notify_mozdefbot'] is False:
                # If the alert tells us to not notify, then don't post message
                message.ack()
                return

            # process valid message
            # see where we send this alert
            channel = options.default_alert_channel
            if 'channel' in body_dict:
                if body_dict['channel'] in options.channels:
                    channel = body_dict['channel']

            # see if we need to delay a bit before sending the alert, to avoid
            # flooding the channel
            if self.lastalert is not None:
                delta = toUTC(datetime.now()) - self.lastalert
                logger.info('new alert, delta since last is {}\n'.format(delta))
                if delta.seconds < 2:
                    logger.info('throttling before writing next alert\n')
                    time.sleep(1)
            self.lastalert = toUTC(datetime.now())
            if len(body_dict['summary']) > 450:
                logger.info('alert is more than 450 bytes, truncating\n')
                body_dict['summary'] = body_dict['summary'][:450] + ' truncated...'

            logger.info("Posting alert: {0}".format(body_dict['summary']))
            self.bot.post_alert_message(body_dict, channel)
            message.ack()
        except ValueError as e:
            logger.exception("mozdefbot_slack exception while processing events queue %r" % e)


def consume_alerts(bot):
    # connect and declare the message queue/kombu objects.
    # server/exchange/queue
    mq_conn_str = 'amqp://{0}:{1}@{2}:{3}//'.format(
        options.mq_user,
        options.mq_password,
        options.mq_alert_server,
        options.mq_port
    )
    mq_alert_conn = Connection(mq_conn_str)

    # Exchange for alerts we pass to plugins
    alert_exchange = Exchange(
        name=options.alert_exchange,
        type='topic',
        durable=True,
        delivery_mode=1
    )

    alert_exchange(mq_alert_conn).declare()

    # Queue for the exchange
    alert_queue = Queue(
        options.queue_name,
        exchange=alert_exchange,
        routing_key=options.alerttopic,
        durable=False,
        no_ack=(not options.mq_ack)
    )
    alert_queue(mq_alert_conn).declare()

    # consume our alerts.
    AlertConsumer(mq_alert_conn, alert_queue, alert_exchange, bot).run()


def init_config():
    options.slack_token = get_config('slack_token', '<CHANGE ME>', options.configfile)
    options.name = get_config('name', 'mozdef', options.configfile)
    options.channels = get_config('channels', 'general', options.configfile).split(',')
    options.default_alert_channel = get_config('default_alert_channel', 'mozdef', options.configfile)

    # queue exchange name
    options.alert_exchange = get_config(
        'alertexchange',
        'alerts',
        options.configfile)

    # queue name
    options.queue_name = get_config(
        'alertqueuename',
        'alertBot',
        options.configfile)

    # queue topic
    options.alerttopic = get_config(
        'alerttopic',
        'mozdef.*',
        options.configfile)

    # how many messages to ask for at once
    options.prefetch = get_config('prefetch', 50, options.configfile)
    options.mq_alert_server = get_config('mqalertserver', 'localhost', options.configfile)
    options.mq_user = get_config('mquser', 'guest', options.configfile)
    options.mq_password = get_config('mqpassword', 'guest', options.configfile)
    options.mq_port = get_config('mqport', 5672, options.configfile)
    # mqack=True sets persistant delivery, False sets transient delivery
    options.mq_ack = get_config('mqack', True, options.configfile)

    # wether or not the bot should send a welcome message upon connecting
    options.notify_welcome = get_config('notify_welcome', True, options.configfile)


if __name__ == "__main__":
    parser = OptionParser()
    parser.add_option(
        "-c", dest='configfile',
        default=sys.argv[0].replace('.py', '.conf'),
        help="configuration file to use")
    (options, args) = parser.parse_args()
    init_config()

    bot = SlackBot(options.slack_token, options.channels, options.name, options.notify_welcome)
    monitor_alerts_thread = Thread(target=consume_alerts, args=[bot])
    monitor_alerts_thread.daemon = True
    monitor_alerts_thread.start()
    bot.run()
