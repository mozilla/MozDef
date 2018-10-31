#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
# Copyright (c) 2017 Mozilla Corporation


import json
import os
import sys
import socket
from configlib import getConfig, OptionParser
from datetime import datetime
import boto.sts
import boto.s3
from boto.sqs.message import RawMessage
import gzip
from StringIO import StringIO
from threading import Timer
import re
import time
from ssl import SSLEOFError, SSLError

from mozdef_util.utilities.toUTC import toUTC
from mozdef_util.elasticsearch_client import ElasticsearchClient, ElasticsearchBadServer, ElasticsearchInvalidIndex, ElasticsearchException
from mozdef_util.utilities.logger import logger, initLogger
from mozdef_util.utilities.to_unicode import toUnicode
from mozdef_util.utilities.remove_at import removeAt

from lib.plugins import sendEventToPlugins, registerPlugins
from lib.sqs import connect_sqs


CLOUDTRAIL_VERB_REGEX = re.compile(r'^([A-Z][^A-Z]*)')

# running under uwsgi?
try:
    import uwsgi
    hasUWSGI = True
except ImportError as e:
    hasUWSGI = False


class RoleManager:
    def __init__(self, region_name='us-east-1', aws_access_key_id=None, aws_secret_access_key=None):
        self.aws_access_key_id = aws_access_key_id
        self.aws_secret_access_key = aws_secret_access_key
        self.credentials = {}
        self.session_credentials = None
        self.session_conn_sts = None
        try:
            self.local_conn_sts = boto.sts.connect_to_region(
                **get_aws_credentials(
                    region_name,
                    self.aws_access_key_id,
                    self.aws_secret_access_key))
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
                creds = get_aws_credentials(
                        region_name,
                        self.session_credentials.access_key,
                        self.session_credentials.secret_key,
                        self.session_credentials.session_token) if self.session_credentials else {}
                self.session_conn_sts = boto.sts.connect_to_region(**creds)
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


def get_aws_credentials(region=None, accesskey=None, secretkey=None, security_token=None):
    result = {}
    if region not in ['', '<add_region>', None]:
        result['region_name'] = region
    if accesskey not in ['', '<add_accesskey>', None]:
        result['aws_access_key_id'] = accesskey
    if secretkey not in ['', '<add_secretkey>', None]:
        result['aws_secret_access_key'] = secretkey
    if security_token not in [None]:
        result['security_token'] = security_token
    return result


def keyMapping(aDict):
    '''map common key/fields to a normalized structure,
       explicitly typed when possible to avoid schema changes for upsteam consumers
       Special accomodations made for logstash,nxlog, beaver, heka and CEF
       Some shippers attempt to conform to logstash-style @fieldname convention.
       This strips the leading at symbol since it breaks some elastic search
       libraries like elasticutils.
    '''
    returndict = dict()

    returndict['source'] = 'cloudtrail'
    returndict['details'] = {}
    returndict['category'] = 'cloudtrail'
    returndict['processid'] = str(os.getpid())
    returndict['processname'] = sys.argv[0]
    returndict['severity'] = 'INFO'
    if 'sourceIPAddress' in aDict and 'eventName' in aDict and 'eventSource' in aDict:
        summary_str = "{0} performed {1} in {2}".format(
            aDict['sourceIPAddress'],
            aDict['eventName'],
            aDict['eventSource']
        )
        returndict['summary'] = summary_str

    if 'eventName' in aDict:
        # Uppercase first character
        aDict['eventName'] = aDict['eventName'][0].upper() + aDict['eventName'][1:]
        returndict['details']['eventVerb'] = CLOUDTRAIL_VERB_REGEX.findall(aDict['eventName'])[0]
        returndict['details']['eventReadOnly'] = (returndict['details']['eventVerb'] in ['Describe', 'Get', 'List'])
    # set the timestamp when we received it, i.e. now
    returndict['receivedtimestamp'] = toUTC(datetime.now()).isoformat()
    returndict['mozdefhostname'] = options.mozdefhostname
    try:
        for k, v in aDict.iteritems():
            k = removeAt(k).lower()

            if k == 'sourceip':
                returndict[u'details']['sourceipaddress'] = v

            elif k == 'sourceipaddress':
                returndict[u'details']['sourceipaddress'] = v

            elif k == 'facility':
                returndict[u'source'] = v

            elif k in ('eventsource'):
                returndict[u'hostname'] = v

            elif k in ('message', 'summary'):
                returndict[u'summary'] = toUnicode(v)

            elif k in ('payload') and 'summary' not in aDict.keys():
                # special case for heka if it sends payload as well as a summary, keep both but move payload to the details section.
                returndict[u'summary'] = toUnicode(v)
            elif k in ('payload'):
                returndict[u'details']['payload'] = toUnicode(v)

            elif k in ('eventtime', 'timestamp', 'utctimestamp', 'date'):
                returndict[u'utctimestamp'] = toUTC(v).isoformat()
                returndict[u'timestamp'] = toUTC(v).isoformat()

            elif k in ('hostname', 'source_host', 'host'):
                returndict[u'hostname'] = toUnicode(v)

            elif k in ('tags'):
                if 'tags' not in returndict.keys():
                    returndict[u'tags'] = []
                if type(v) == list:
                    returndict[u'tags'] += v
                else:
                    if len(v) > 0:
                        returndict[u'tags'].append(v)

            # nxlog keeps the severity name in syslogseverity,everyone else should use severity or level.
            elif k in ('syslogseverity', 'severity', 'severityvalue', 'level', 'priority'):
                returndict[u'severity'] = toUnicode(v).upper()

            elif k in ('facility', 'syslogfacility'):
                returndict[u'facility'] = toUnicode(v)

            elif k in ('pid', 'processid'):
                returndict[u'processid'] = toUnicode(v)

            # nxlog sets sourcename to the processname (i.e. sshd), everyone else should call it process name or pname
            elif k in ('pname', 'processname', 'sourcename', 'program'):
                returndict[u'processname'] = toUnicode(v)

            # the file, or source
            elif k in ('path', 'logger', 'file'):
                returndict[u'eventsource'] = toUnicode(v)

            elif k in ('type', 'eventtype', 'category'):
                returndict[u'category'] = toUnicode(v)

            # custom fields as a list/array
            elif k in ('fields', 'details'):
                if type(v) is not dict:
                    returndict[u'details'][u'message'] = v
                else:
                    if len(v) > 0:
                        for details_key, details_value in v.iteritems():
                            returndict[u'details'][details_key] = details_value

            # custom fields/details as a one off, not in an array
            # i.e. fields.something=value or details.something=value
            # move them to a dict for consistency in querying
            elif k.startswith('fields.') or k.startswith('details.'):
                newName = k.replace('fields.', '')
                newName = newName.lower().replace('details.', '')
                # add a dict to hold the details if it doesn't exist
                if 'details' not in returndict.keys():
                    returndict[u'details'] = dict()
                # add field with a special case for shippers that
                # don't send details
                # in an array as int/floats/strings
                # we let them dictate the data type with field_datatype
                # convention
                if newName.endswith('_int'):
                    returndict[u'details'][unicode(newName)] = int(v)
                elif newName.endswith('_float'):
                    returndict[u'details'][unicode(newName)] = float(v)
                else:
                    returndict[u'details'][unicode(newName)] = toUnicode(v)
            else:
                returndict[u'details'][k] = v

        if 'utctimestamp' not in returndict.keys():
            # default in case we don't find a reasonable timestamp
            returndict['utctimestamp'] = toUTC(datetime.now()).isoformat()
    except Exception as e:
        logger.exception(e)
        logger.error('Malformed message: %r' % aDict)

    return returndict


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
        if options.cloudtrail_arn not in ['<cloudtrail_arn>', 'cloudtrail_arn']:
            role_manager_args = {}

            role_manager = RoleManager(**get_aws_credentials(
                options.region,
                options.accesskey,
                options.secretkey))
            role_manager.assume_role(options.cloudtrail_arn)
            role_creds = role_manager.get_credentials(options.cloudtrail_arn)
        else:
            role_creds = {}
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
            except (SSLEOFError, SSLError, socket.error) as e:
                logger.info('Received network related error...reconnecting')
                time.sleep(5)
                self.connection, self.taskQueue = connect_sqs(
                    task_exchange=options.taskexchange,
                    **get_aws_credentials(
                        options.region,
                        options.accesskey,
                        options.secretkey))
                self.taskQueue.set_message_class(RawMessage)

    def on_message(self, body):
        # print("RECEIVED MESSAGE: %r" % (body, ))
        try:
            # default elastic search metadata for an event
            metadata = {
                'index': 'events',
                'doc_type': 'cloudtrail',
                'id': None
            }
            # just to be safe..check what we were sent.
            if isinstance(body, dict):
                bodyDict = body
            elif isinstance(body, str) or isinstance(body, unicode):
                try:
                    bodyDict = json.loads(body)   # lets assume it's json
                except ValueError as e:
                    # not json..ack but log the message
                    logger.error("Unknown body type received %r" % body)
                    return
            else:
                logger.error("Unknown body type received %r\n" % body)
                return

            if 'customendpoint' in bodyDict.keys() and bodyDict['customendpoint']:
                # custom document
                # send to plugins to allow them to modify it if needed
                (normalizedDict, metadata) = sendEventToPlugins(bodyDict, metadata, pluginList)
            else:
                # normalize the dict
                # to the mozdef events standard
                normalizedDict = keyMapping(bodyDict)

                # send to plugins to allow them to modify it if needed
                if normalizedDict is not None and isinstance(normalizedDict, dict) and normalizedDict.keys():
                    (normalizedDict, metadata) = sendEventToPlugins(normalizedDict, metadata, pluginList)

            # drop the message if a plug in set it to None
            # signaling a discard
            if normalizedDict is None:
                return

            # make a json version for posting to elastic search
            jbody = json.JSONEncoder().encode(normalizedDict)

            try:
                bulk = False
                if options.esbulksize != 0:
                    bulk = True

                bulk = False
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
                    # state may be already set.
                    return
            except ElasticsearchException as e:
                # exception target for queue capacity issues reported by elastic search so catch the error, report it and retry the message
                try:
                    logger.exception('ElasticSearchException: {0} reported while indexing event'.format(e))
                    return
                except kombu.exceptions.MessageStateError:
                    # state may be already set.
                    return
        except Exception as e:
            logger.exception(e)
            logger.error('Malformed message: %r' % body)


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

    sqs_conn, eventTaskQueue = connect_sqs(
        task_exchange=options.taskexchange,
        **get_aws_credentials(
            options.region,
            options.accesskey,
            options.secretkey))
    # consume our queue
    taskConsumer(sqs_conn, eventTaskQueue, es).run()


def initConfig():
    # capture the hostname
    options.mozdefhostname = getConfig('mozdefhostname', socket.gethostname(), options.configfile)

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

    # aws options
    options.accesskey = getConfig('accesskey', '', options.configfile)
    options.secretkey = getConfig('secretkey', '', options.configfile)
    options.region = getConfig('region', '', options.configfile)

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

    pluginList = registerPlugins()

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
