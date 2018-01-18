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
import boto.sqs
import boto.sts
import boto.s3
from boto.sqs.message import RawMessage
import gzip
from StringIO import StringIO
from threading import Timer
import re

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../lib'))
from utilities.toUTC import toUTC
from elasticsearch_client import ElasticsearchClient
from utilities.logger import logger, initLogger


CLOUDTRAIL_VERB_REGEX = re.compile(r'^([A-Z][^A-Z]*)')

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
                self.session_conn_sts = boto.sts.connect_to_region(
                    'us-east-1',
                    **self.get_credential_arguments(self.session_credentials)
                )
            except Exception, e:
                logger.error("Unable to connect to STS with session token due to exception %s" % e.message)
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

    def __init__(self, mqConnection, taskQueue, esConnection):
        self.connection = mqConnection
        self.esConnection = esConnection
        self.taskQueue = taskQueue
        self.s3_connection = None
        # This value controls how long we sleep
        # between reauthenticating and getting a new set of creds
        self.flush_wait_time = 1800

        if options.esbulksize != 0:
            # if we are bulk posting enable a timer to occasionally flush the bulker even if it's not full
            # to prevent events from sticking around an idle worker
            self.esConnection.start_bulk_timer()

        self.authenticate()
        # This cycles the role manager creds every 30 minutes
        # or else we would be getting errors after a while
        Timer(self.flush_wait_time, self.flush_s3_creds).start()

    def authenticate(self):
        role_manager = RoleManager(options.accesskey, options.secretkey)
        role_manager.assume_role(options.cloudtrail_arn)
        role_creds = role_manager.get_credentials(options.cloudtrail_arn)
        self.s3_connection = boto.connect_s3(**role_creds)

    def flush_s3_creds(self):
        logger.debug('Recycling credentials and reassuming role')
        self.authenticate()
        Timer(self.flush_wait_time, self.flush_s3_creds).start()

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
                records = self.taskQueue.get_messages(options.prefetch)
                for msg in records:
                    body_message = msg.get_body()
                    event = json.loads(body_message)

                    if not event['Message']:
                        logger.error('Invalid message format for cloudtrail SQS messages')
                        logger.error('Malformed Message: %r' % body_message)
                        continue

                    if event['Message'] == 'CloudTrail validation message.':
                        # We don't care about these messages
                        continue

                    message_json = json.loads(event['Message'])

                    if 's3ObjectKey' not in message_json.keys():
                        logger.error('Invalid message format, expecting an s3ObjectKey in Message')
                        logger.error('Malformed Message: %r' % body_message)
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
                logger.exception('Exception while handling message: %r' % e)
            except Exception as e:
                logger.exception(e)
                time.sleep(3)

            time.sleep(.1)

    def on_message(self, message):
        try:
            returndict = dict()

            returndict['category'] = 'cloudtrail'
            returndict['source'] = 'cloudtrail'
            returndict['details'] = {}
            returndict['utctimestamp'] = toUTC(message['eventTime']).isoformat()
            returndict['receivedtimestamp'] = toUTC(datetime.now()).isoformat()
            returndict['mozdefhostname'] = socket.gethostname()
            returndict['hostname'] = message['eventSource']
            returndict['processid'] = str(os.getpid())
            returndict['processname'] = sys.argv[0]
            returndict['severity'] = 'INFO'
            returndict['tags'] = ['cloudtrail']

            if 'sourceIPAddress' in message and 'eventName' in message and 'eventSource' in message:
                summary_str = "{0} performed {1} in {2}".format(
                    message['sourceIPAddress'],
                    message['eventName'],
                    message['eventSource']
                )
                returndict['summary'] = summary_str

            if 'eventName' in message:
                # Uppercase first character
                verb_name = message['eventName'][0].upper() + message['eventName'][1:]
                returndict['eventVerb'] = CLOUDTRAIL_VERB_REGEX.findall(verb_name)[0]
                returndict['eventReadOnly'] = (returndict['eventVerb'] in ['Describe', 'Get', 'List'])

            # Save original message for now since we're dropping other fields
            returndict['raw_msg'] = json.dumps(message)

            es.save_event(body=returndict, doc_type='cloudtrail', bulk=True)
        except Exception as e:
            logger.exception(e)
            logger.error('Malformed message: %r' % message)


def main():
    # meant only to talk to SQS using boto
    # and process events as json.

    if hasUWSGI:
        logger.info("started as uwsgi mule {0}".format(uwsgi.mule_id()))
    else:
        logger.info('started without uwsgi')

    if options.mqprotocol not in ('sqs'):
        logger.error('Can only process SQS queues, terminating')
        sys.exit(1)

    sqs_conn = boto.sqs.connect_to_region(options.region, aws_access_key_id=options.accesskey, aws_secret_access_key=options.secretkey)
    # attach to the queue
    eventTaskQueue = sqs_conn.get_queue(options.taskexchange)

    # consume our queue
    taskConsumer(sqs_conn, eventTaskQueue, es).run()


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

    main()
