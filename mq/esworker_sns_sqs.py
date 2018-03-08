#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
# Copyright (c) 2017 Mozilla Corporation


import json
import os

import sys
import socket
import time
from configlib import getConfig, OptionParser
from datetime import datetime
import pytz

import boto.sqs
from boto.sqs.message import RawMessage
import kombu

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../lib'))
from utilities.toUTC import toUTC
from utilities.logger import logger, initLogger
from elasticsearch_client import ElasticsearchClient, ElasticsearchBadServer, ElasticsearchInvalidIndex, ElasticsearchException

from lib.plugins import sendEventToPlugins, registerPlugins


# running under uwsgi?
try:
    import uwsgi
    hasUWSGI = True
except ImportError as e:
    hasUWSGI = False


def esConnect():
    '''open or re-open a connection to elastic search'''
    return ElasticsearchClient((list('{0}'.format(s) for s in options.esservers)), options.esbulksize)


class taskConsumer(object):

    def __init__(self, mqConnection, taskQueue, esConnection, options):
        self.connection = mqConnection
        self.esConnection = esConnection
        self.taskQueue = taskQueue

        self.pluginList = registerPlugins()

        self.options = options

        if self.options.esbulksize != 0:
            # if we are bulk posting enable a timer to occasionally flush the bulker even if it's not full
            # to prevent events from sticking around an idle worker
            self.esConnection.start_bulk_timer()

    def run(self):
        self.taskQueue.set_message_class(RawMessage)

        while True:
            try:
                records = self.taskQueue.get_messages(self.options.prefetch)
                for msg in records:
                    msg_body = msg.get_body()
                    try:
                        # get_body() should be json
                        message_json = json.loads(msg_body)
                        self.on_message(message_json)
                        # delete message from queue
                        self.taskQueue.delete_message(msg)
                    except ValueError:
                        logger.error('Invalid message, not JSON <dropping message and continuing>: %r' % msg_body)
                        self.taskQueue.delete_message(msg)
                        continue
                time.sleep(.1)
            except Exception as e:
                logger.exception(e)
                sys.exit(1)

    def on_message(self, message):
        try:
            # default elastic search metadata for an event
            metadata = {
                'index': 'events',
                'id': None
            }
            event = {}

            event['receivedtimestamp'] = toUTC(datetime.now()).isoformat()
            event['mozdefhostname'] = self.options.mozdefhostname

            if 'tags' in event:
                event['tags'].extend([self.options.taskexchange])
            else:
                event['tags'] = [self.options.taskexchange]

            event['severity'] = 'INFO'

            # Set defaults
            event['processid'] = ''
            event['processname'] = ''
            event['category'] = 'syslog'

            for message_key, message_value in message.iteritems():
                if 'Message' == message_key:
                    try:
                        message_json = json.loads(message_value)
                        for inside_message_key, inside_message_value in message_json.iteritems():
                            if inside_message_key in ('processid', 'pid'):
                                processid = str(inside_message_value)
                                processid = processid.replace('[', '')
                                processid = processid.replace(']', '')
                                event['processid'] = processid
                            elif inside_message_key in ('pname'):
                                event['processname'] = inside_message_value
                            elif inside_message_key in ('hostname'):
                                event['hostname'] = inside_message_value
                            elif inside_message_key in ('time', 'timestamp'):
                                event['timestamp'] = toUTC(inside_message_value).isoformat()
                                event['utctimestamp'] = toUTC(event['timestamp']).astimezone(pytz.utc).isoformat()
                            elif inside_message_key in ('type'):
                                event['category'] = inside_message_value
                            elif inside_message_key in ('payload', 'message'):
                                event['summary'] = inside_message_value
                            else:
                                if 'details' not in event:
                                    event['details'] = {}
                                event['details'][inside_message_key] = inside_message_value
                    except ValueError:
                        event['summary'] = message_value
            (event, metadata) = sendEventToPlugins(event, metadata, self.pluginList)
            # Drop message if plugins set to None
            if event is None:
                return
            self.save_event(event, metadata)
        except Exception as e:
            logger.exception(e)
            logger.error('Malformed message: %r' % message)

    def save_event(self, event, metadata):
        try:
            # drop the message if a plug in set it to None
            # signaling a discard
            if event is None:
                return

            # make a json version for posting to elastic search
            jbody = json.JSONEncoder().encode(event)

            try:
                bulk = False
                if self.options.esbulksize != 0:
                    bulk = True

                self.esConnection.save_event(
                    index=metadata['index'],
                    doc_id=metadata['id'],
                    body=jbody,
                    bulk=bulk
                )

            except (ElasticsearchBadServer, ElasticsearchInvalidIndex) as e:
                # handle loss of server or race condition with index rotation/creation/aliasing
                try:
                    self.esConnection = esConnect()
                    return
                except kombu.exceptions.MessageStateError:
                    return
            except ElasticsearchException as e:
                logger.exception('ElasticSearchException: {0} reported while indexing event'.format(e))
                logger.error('Malformed jbody: %r' % jbody)
                return
        except Exception as e:
            logger.exception(e)
            logger.error('Malformed message: %r' % event)


def main():
    if hasUWSGI:
        logger.info("started as uwsgi mule {0}".format(uwsgi.mule_id()))
    else:
        logger.info('started without uwsgi')

    if options.mqprotocol not in ('sqs'):
        logger.error('Can only process SQS queues, terminating')
        sys.exit(1)

    mqConn = boto.sqs.connect_to_region(options.region, aws_access_key_id=options.accesskey, aws_secret_access_key=options.secretkey)
    # attach to the queue
    eventTaskQueue = mqConn.get_queue(options.taskexchange)

    # consume our queue
    taskConsumer(mqConn, eventTaskQueue, es, options).run()


def initConfig():
    # capture the hostname
    options.mozdefhostname = getConfig('mozdefhostname', socket.gethostname(), options.configfile)

    # elastic search options. set esbulksize to a non-zero value to enable bulk posting, set timeout to post no matter how many events after X seconds.
    options.esservers = list(getConfig('esservers', 'http://localhost:9200', options.configfile).split(','))
    options.esbulksize = getConfig('esbulksize', 0, options.configfile)
    options.esbulktimeout = getConfig('esbulktimeout', 30, options.configfile)

    # set to sqs for Amazon
    options.mqprotocol = getConfig('mqprotocol', 'sqs', options.configfile)

    # rabbit message queue options
    options.taskexchange = getConfig('taskexchange', 'eventtask', options.configfile)
    # rabbit: how many messages to ask for at once from the message queue
    options.prefetch = getConfig('prefetch', 10, options.configfile)

    # aws options
    options.accesskey = getConfig('accesskey', '', options.configfile)
    options.secretkey = getConfig('secretkey', '', options.configfile)
    options.region = getConfig('region', 'us-west-1', options.configfile)

    # plugin options
    # secs to pass before checking for new/updated plugins
    # seems to cause memory leaks..
    # regular updates are disabled for now,
    # though we set the frequency anyway.
    options.plugincheckfrequency = getConfig('plugincheckfrequency', 120, options.configfile)


if __name__ == '__main__':
    # configure ourselves
    parser = OptionParser()
    parser.add_option("-c", dest='configfile', default=sys.argv[0].replace('.py', '.conf'), help="configuration file to use")
    (options, args) = parser.parse_args()
    initConfig()
    initLogger(options)

    # open ES connection globally so we don't waste time opening it per message
    es = esConnect()
    main()
