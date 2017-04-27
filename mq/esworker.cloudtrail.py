#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
# Copyright (c) 2017 Mozilla Corporation
#
# Contributors:
# Brandon Myers bmyers@mozilla.com


import json
import os
import pynsive
import sys
import socket
import time
from configlib import getConfig, OptionParser
from datetime import datetime, timedelta
from operator import itemgetter
import boto.sqs
import boto.sts
import boto.s3
from boto.sqs.message import RawMessage
import gzip
from StringIO import StringIO

import sys
import os
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../lib'))
from utilities.toUTC import toUTC
from elasticsearch_client import ElasticsearchClient
from utilities.logger import logger, initLogger


# running under uwsgi?
try:
    import uwsgi
    hasUWSGI = True
except ImportError as e:
    hasUWSGI = False


class RoleManager:
    def __init__(self, aws_access_key_id=None, aws_secret_access_key=None):
        self.aws_access_key_id = aws_access_key_id
        self.aws_secret_access_key = aws_secret_access_key
        self.credentials = {}
        self.session_credentials = None
        self.session_conn_sts = None
        try:
            self.local_conn_sts = boto.sts.connect_to_region(
                'us-east-1',
                aws_access_key_id=self.aws_access_key_id,
                aws_secret_access_key=self.aws_secret_access_key
            )
        except Exception, e:
            logger.error("Unable to connect to STS due to exception %s" % e.message)
            raise

        if self.aws_access_key_id is not None or self.aws_secret_access_key is not None:
            # We're using API credentials not an IAM Role
            try:
                if self.session_credentials is None or self.session_credentials.is_expired():
                    self.session_credentials = self.local_conn_sts.get_session_token()
            except Exception, e:
                logger.error("Unable to get session token due to exception %s" % e.message)
                raise
            try:
                self.session_conn_sts = boto.sts.connect_to_region('us-east-1',
                                **self.get_credential_arguments(self.session_credentials))
            except Exception, e:
                logger.error("Unable to connect to STS with session token due to exception %s" %
                              e.message)
                raise
            self.conn_sts = self.session_conn_sts
        else:
            self.conn_sts = self.local_conn_sts

    def assume_role(self,
                    role_arn,
                    role_session_name='unknown',
                    policy=None):
        '''Return a boto.sts.credential.Credential object given a role_arn.
        First check if a Credential oject exists in the local self.credentials
        cache that is not expired. If there isn't one, assume the role of role_arn
        store the Credential in the credentials cache and return it'''
        logger.debug("Connecting to sts")
        if role_arn in self.credentials:
            if not self.credentials[role_arn] or not self.credentials[role_arn].is_expired():
                # Return the cached value if it's False (indicating a permissions issue) or if
                # it hasn't expired.
                return self.credentials[role_arn]
        try:
            self.credentials[role_arn] = self.conn_sts.assume_role(
                role_arn=role_arn,
                role_session_name=role_session_name,
                policy=policy).credentials
            logger.debug("Assumed new role with credential %s" % self.credentials[role_arn].to_dict())
        except Exception, e:
            print e
            logger.error("Unable to assume role %s due to exception %s" % (role_arn, e.message))
            self.credentials[role_arn] = False
        return self.credentials[role_arn]

    def get_credentials(self,
                        role_arn,
                        role_session_name='unknown',
                        policy=None):
        '''Assume the role of role_arn, and return a credential dictionary for that role'''
        credential = self.assume_role(role_arn,
                                      role_session_name,
                                      policy)
        return self.get_credential_arguments(credential)

    def get_credential_arguments(self, credential):
        '''Given a boto.sts.credential.Credential object, return a dictionary of get_credential_arguments
        usable as kwargs with a boto connect method'''
        return {
            'aws_access_key_id': credential.access_key,
            'aws_secret_access_key': credential.secret_key,
            'security_token': credential.session_token} if credential else {}


def esConnect():
    '''open or re-open a connection to elastic search'''
    return ElasticsearchClient(
        (list('{0}'.format(s) for s in options.esservers)),
        bulk_amount=options.esbulksize,
        bulk_refresh_time=options.esbulktimeout
    )


class taskConsumer(object):

    def __init__(self, mqConnection, taskQueue, esConnection, s3_connection):
        self.connection = mqConnection
        self.esConnection = esConnection
        self.taskQueue = taskQueue
        self.s3_connection = s3_connection

        if options.esbulksize != 0:
            # if we are bulk posting enable a timer to occasionally flush the bulker even if it's not full
            # to prevent events from sticking around an idle worker
            self.esConnection.start_bulk_timer()

    def process_file(self, s3file):
        logger.debug("Fetching %s" % s3file.name)
        compressedData = s3file.read()
        databuf = StringIO(compressedData)
        gzip_file = gzip.GzipFile(fileobj=databuf)
        json_logs = json.loads(gzip_file.read())
        return json_logs['Records']

    def run(self):
        self.taskQueue.set_message_class(RawMessage)
        while True:
            try:
                # We only want to get one record, since this contains a gzip file
                # containing all of the events
                records = self.taskQueue.get_messages(1)
                for msg in records:
                    body_message = msg.get_body()
                    event = json.loads(body_message)

                    if not event['Message']:
                        logger.error('Invalid message format for cloudtrail SQS messages')
                        continue

                    message_json = json.loads(event['Message'])
                    if 's3ObjectKey' not in message_json.keys():
                        logger.error('Invalid message format, expecting an s3ObjectKey in Message')
                        continue

                    s3_log_files = message_json['s3ObjectKey']
                    for log_file in s3_log_files:
                        logger.debug('Downloading and parsing ' + log_file)
                        bucket = self.s3_connection.get_bucket(message_json['s3Bucket'])

                        log_file_lookup = bucket.lookup(log_file)
                        events = self.process_file(log_file_lookup)
                        for event in events:
                            self.on_message(event)

                    self.taskQueue.delete_message(msg)

            except KeyboardInterrupt:
                sys.exit(1)
            except ValueError as e:
                logger.error('Exception while handling message: %r' % e)
                sys.exit(1)
            except Exception as e:
                logger.error('Exception received: %r' % e)

            time.sleep(.1)

    def on_message(self, message):
        message['category'] = 'cloudtrail'
        message['utctimestamp'] = toUTC(message['eventTime']).isoformat()
        message['receivedtimestamp'] = toUTC(datetime.now()).isoformat()
        message['mozdefhostname'] = socket.gethostname()
        message['hostname'] = message['eventSource']
        message['processid'] = os.getpid()
        message['processname'] = sys.argv[0]
        message['severity'] = 'INFO'
        summary_str = "{0} performed {1} in {2}".format(
            message['sourceIPAddress'],
            message['eventName'],
            message['eventSource']
        )
        message['summary'] = summary_str
        es.save_event(body=message, doc_type='cloudtrail', bulk=True)


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


def checkPlugins(pluginList, lastPluginCheck):
    if abs(datetime.now() - lastPluginCheck).seconds > options.plugincheckfrequency:
        # print('[*] checking plugins')
        lastPluginCheck = datetime.now()
        pluginList = registerPlugins()
        return pluginList, lastPluginCheck
    else:
        return pluginList, lastPluginCheck


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
                for d in dict2List(v):
                    yield d
            else:
                yield v
    else:
        yield ''


def sendEventToPlugins(anevent, metadata, pluginList):
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
                return (anevent, metadata)
        if send:
            (anevent, metadata) = plugin[0].onMessage(anevent, metadata)
            if anevent is None:
                # plug-in is signalling to drop this message
                # early exit
                return (anevent, metadata)

    return (anevent, metadata)


def main():
    # meant only to talk to SQS using boto
    # and process events as json.

    if hasUWSGI:
        sys.stdout.write("started as uwsgi mule {0}\n".format(uwsgi.mule_id()))
    else:
        sys.stdout.write('started without uwsgi\n')

    if options.mqprotocol not in ('sqs'):
        sys.stdout.write('Can only process SQS queues, terminating\n')
        sys.exit(1)

    sqs_conn = boto.sqs.connect_to_region(options.region, aws_access_key_id=options.accesskey, aws_secret_access_key=options.secretkey)
    # attach to the queue
    eventTaskQueue = sqs_conn.get_queue(options.taskexchange)

    role_manager = RoleManager(options.accesskey, options.secretkey)
    role_manager.assume_role(options.cloudtrail_arn)
    role_creds = role_manager.get_credentials(options.cloudtrail_arn)
    s3_conn = boto.connect_s3(**role_creds)

    # consume our queue
    taskConsumer(sqs_conn, eventTaskQueue, es, s3_conn).run()


def initConfig():
    # output our log to stdout or syslog
    options.output = getConfig('output', 'stdout', options.configfile)
    options.sysloghostname = getConfig('sysloghostname', 'localhost', options.configfile)
    options.syslogport = getConfig('syslogport', 514, options.configfile)

    # elastic search options. set esbulksize to a non-zero value to enable bulk posting, set timeout to post no matter how many events after X seconds.
    options.esservers = list(getConfig('esservers', 'http://localhost:9200', options.configfile).split(','))
    options.esbulksize = getConfig('esbulksize', 0, options.configfile)
    options.esbulktimeout = getConfig('esbulktimeout', 30, options.configfile)

    # set to sqs for Amazon
    options.mqprotocol = getConfig('mqprotocol', 'sqs', options.configfile)

    # rabbit message queue options
    options.mqserver = getConfig('mqserver', 'localhost', options.configfile)
    options.taskexchange = getConfig('taskexchange', 'eventtask', options.configfile)
    options.eventexchange = getConfig('eventexchange', 'events', options.configfile)
    # rabbit: how many messages to ask for at once from the message queue
    options.prefetch = getConfig('prefetch', 10, options.configfile)
    # rabbit: user creds
    options.mquser = getConfig('mquser', 'guest', options.configfile)
    options.mqpassword = getConfig('mqpassword', 'guest', options.configfile)
    # rabbit: port/vhost
    options.mqport = getConfig('mqport', 5672, options.configfile)
    options.mqvhost = getConfig('mqvhost', '/', options.configfile)

    # rabbit: run with message acking?
    # also toggles transient/persistant delivery (messages in memory only or stored on disk)
    # ack=True sets persistant delivery, False sets transient delivery
    options.mqack = getConfig('mqack', True, options.configfile)

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

    # This is the full ARN that the s3 bucket lives under
    options.cloudtrail_arn = getConfig('cloudtrail_arn', 'cloudtrail_arn', options.configfile)


if __name__ == '__main__':
    # configure ourselves
    parser = OptionParser()
    parser.add_option("-c", dest='configfile', default=sys.argv[0].replace('.py', '.conf'), help="configuration file to use")
    (options, args) = parser.parse_args()
    initConfig()
    initLogger(options)

    # open ES connection globally so we don't waste time opening it per message
    es = esConnect()

    # force a check for plugins and establish the plugin list
    pluginList = list()
    lastPluginCheck = datetime.now() - timedelta(minutes=60)
    pluginList, lastPluginCheck = checkPlugins(pluginList, lastPluginCheck)
    main()
