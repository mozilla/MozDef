#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
# Copyright (c) 2017 Mozilla Corporation


import json

import sys
import socket
import time
from configlib import getConfig, OptionParser
from datetime import datetime
import pytz

from boto.sqs.message import RawMessage
import kombu
from ssl import SSLEOFError, SSLError

from mozdef_util.utilities.toUTC import toUTC
from mozdef_util.utilities.logger import logger, initLogger
from mozdef_util.elasticsearch_client import ElasticsearchClient, ElasticsearchBadServer, ElasticsearchInvalidIndex, ElasticsearchException

from lib.aws import get_aws_credentials
from lib.plugins import sendEventToPlugins, registerPlugins
from lib.sqs import connect_sqs


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
            except (SSLEOFError, SSLError, socket.error):
                logger.info('Received network related error...reconnecting')
                time.sleep(5)
                self.connection, self.taskQueue = connect_sqs(
                    options.region,
                    options.accesskey,
                    options.secretkey,
                    options.taskexchange
                )
                self.taskQueue.set_message_class(RawMessage)

    def on_message(self, message):
        try:
            # default elastic search metadata for an event
            metadata = {
                'index': 'events',
                'doc_type': 'event',
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
            event['details'] = {}

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
                            elif inside_message_key in ('processname','pname'):
                                event['processname'] = inside_message_value
                            elif inside_message_key in ('hostname'):
                                event['hostname'] = inside_message_value
                            elif inside_message_key in ('time', 'timestamp'):
                                event['timestamp'] = toUTC(inside_message_value).isoformat()
                                event['utctimestamp'] = toUTC(event['timestamp']).astimezone(pytz.utc).isoformat()
                            elif inside_message_key in ('type', 'category'):
                                event['category'] = inside_message_value
                            elif inside_message_key in ('summary','payload', 'message'):
                                event['summary'] = inside_message_value
                            elif inside_message_key in ('source'):
                                event['source'] = inside_message_value
                            elif inside_message_key in ('fields', 'details'):
                                if type(inside_message_value) is not dict:
                                    event[u'details'][u'message'] = inside_message_value
                                else:
                                    if len(inside_message_value) > 0:
                                        for details_key, details_value in inside_message_value.iteritems():
                                            event[u'details'][details_key] = details_value
                            else:
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
                    doc_type=metadata['doc_type'],
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

    sqs_conn, eventTaskQueue = connect_sqs(
        task_exchange=options.taskexchange,
        **get_aws_credentials(
            options.region,
            options.accesskey,
            options.secretkey))
    # consume our queue
    taskConsumer(sqs_conn, eventTaskQueue, es, options).run()


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
    options.region = getConfig('region', '', options.configfile)

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

    try:
        main()
    except KeyboardInterrupt as e:
        logger.info("Exiting worker")
        if options.esbulksize != 0:
            es.finish_bulk()
    except Exception as e:
        if options.esbulksize != 0:
            es.finish_bulk()
        raise
