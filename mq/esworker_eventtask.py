#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
# Copyright (c) 2014 Mozilla Corporation


import json
import kombu
import os
import sys
import socket
from configlib import getConfig, OptionParser
from datetime import datetime
from kombu import Connection, Queue, Exchange
from kombu.mixins import ConsumerMixin

sys.path.append(os.path.join(os.path.dirname(__file__), "../lib"))
from elasticsearch_client import ElasticsearchClient, ElasticsearchBadServer, ElasticsearchInvalidIndex, ElasticsearchException

from utilities.toUTC import toUTC
from utilities.to_unicode import toUnicode
from utilities.remove_at import removeAt
from utilities.is_cef import isCEF

from lib.plugins import sendEventToPlugins, registerPlugins


# running under uwsgi?
try:
    import uwsgi
    hasUWSGI = True
except ImportError as e:
    hasUWSGI = False


def keyMapping(aDict):
    '''map common key/fields to a normalized structure,
       explicitly typed when possible to avoid schema changes for upsteam consumers
       Special accomodations made for logstash,nxlog, beaver, heka and CEF
       Some shippers attempt to conform to logstash-style @fieldname convention.
       This strips the leading at symbol since it breaks some elastic search
       libraries like elasticutils.
    '''
    returndict = dict()

    # uncomment to save the source event for debugging, or chain of custody/forensics
    # returndict['original']=aDict

    # set the timestamp when we received it, i.e. now
    returndict['receivedtimestamp'] = toUTC(datetime.now()).isoformat()
    returndict['mozdefhostname'] = options.mozdefhostname
    try:
        for k, v in aDict.iteritems():
            k = removeAt(k).lower()

            if k == 'sourceip':
                if 'details' not in returndict.keys():
                    returndict[u'details'] = dict()
                returndict[u'details']['sourceipaddress'] = v

            if k == 'facility':
                returndict[u'source'] = v

            if k in ('message', 'summary'):
                returndict[u'summary'] = toUnicode(v)

            if k in ('payload') and 'summary' not in aDict.keys():
                # special case for heka if it sends payload as well as a summary, keep both but move payload to the details section.
                returndict[u'summary'] = toUnicode(v)
            elif k in ('payload'):
                if 'details' not in returndict.keys():
                    returndict[u'details'] = dict()
                returndict[u'details']['payload'] = toUnicode(v)

            if k in ('eventtime', 'timestamp', 'utctimestamp', 'date'):
                returndict[u'utctimestamp'] = toUTC(v).isoformat()
                returndict[u'timestamp'] = toUTC(v).isoformat()

            if k in ('hostname', 'source_host', 'host'):
                returndict[u'hostname'] = toUnicode(v)

            if k in ('tags'):
                if 'tags' not in returndict.keys():
                    returndict[u'tags'] = []
                if type(v) == list:
                    returndict[u'tags'] += v
                else:
                    if len(v) > 0:
                        returndict[u'tags'].append(v)

            # nxlog keeps the severity name in syslogseverity,everyone else should use severity or level.
            if k in ('syslogseverity', 'severity', 'severityvalue', 'level', 'priority'):
                returndict[u'severity'] = toUnicode(v).upper()

            if k in ('facility', 'syslogfacility'):
                returndict[u'facility'] = toUnicode(v)

            if k in ('pid', 'processid'):
                returndict[u'processid'] = toUnicode(v)

            # nxlog sets sourcename to the processname (i.e. sshd), everyone else should call it process name or pname
            if k in ('pname', 'processname', 'sourcename', 'program'):
                returndict[u'processname'] = toUnicode(v)

            # the file, or source
            if k in ('path', 'logger', 'file'):
                returndict[u'eventsource'] = toUnicode(v)

            if k in ('type', 'eventtype', 'category'):
                returndict[u'category'] = toUnicode(v)

            # custom fields as a list/array
            if k in ('fields', 'details'):
                if len(v) > 0:
                    returndict[u'details'] = v

            # custom fields/details as a one off, not in an array
            # i.e. fields.something=value or details.something=value
            # move them to a dict for consistency in querying
            if k.startswith('fields.') or k.startswith('details.'):
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


        #nxlog windows log handling
        if 'Domain' in aDict.keys() and 'SourceModuleType' in aDict.keys():
            # add a dict to hold the details if it doesn't exist
            if 'details' not in returndict.keys():
                returndict[u'details'] = dict()

            # nxlog parses all windows event fields very well
            # copy all fields to details
            returndict[u'details'][k]=v

        if 'utctimestamp' not in returndict.keys():
            # default in case we don't find a reasonable timestamp
            returndict['utctimestamp'] = toUTC(datetime.now()).isoformat()

    except Exception as e:
        sys.stderr.write('esworker exception normalizing the message %r\n' % e)
        return None

    return returndict


def esConnect():
    '''open or re-open a connection to elastic search'''
    return ElasticsearchClient((list('{0}'.format(s) for s in options.esservers)), options.esbulksize)


class taskConsumer(ConsumerMixin):

    def __init__(self, mqConnection, taskQueue, topicExchange, esConnection):
        self.connection = mqConnection
        self.esConnection = esConnection
        self.taskQueue = taskQueue
        self.topicExchange = topicExchange
        self.mqproducer = self.connection.Producer(serializer='json')
        if hasUWSGI:
            self.muleid = uwsgi.mule_id()
        else:
            self.muleid = 0
        if options.esbulksize != 0:
            # if we are bulk posting enable a timer to occasionally flush the bulker even if it's not full
            # to prevent events from sticking around an idle worker
            self.esConnection.start_bulk_timer()

    def get_consumers(self, Consumer, channel):
        consumer = Consumer(self.taskQueue, callbacks=[self.on_message], accept=['json', 'text/plain'], no_ack=(not options.mqack))
        consumer.qos(prefetch_count=options.prefetch)
        return [consumer]

    def on_message(self, body, message):
        # print("RECEIVED MESSAGE: %r" % (body, ))
        try:
            # default elastic search metadata for an event
            metadata = {
                'index': 'events',
                'doc_type': 'event',
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
                    sys.stderr.write("esworker exception: unknown body type received %r\n" % body)
                    message.ack()
                    return
            else:
                sys.stderr.write("esworker exception: unknown body type received %r\n" % body)
                message.ack()
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
                message.ack()
                return

            # make a json version for posting to elastic search
            jbody = json.JSONEncoder().encode(normalizedDict)

            if isCEF(normalizedDict):
                # cef records are set to the 'deviceproduct' field value.
                metadata['doc_type'] = 'cef'
                if 'details' in normalizedDict.keys() and 'deviceproduct' in normalizedDict['details'].keys():
                    # don't create strange doc types..
                    if ' ' not in normalizedDict['details']['deviceproduct'] and '.' not in normalizedDict['details']['deviceproduct']:
                        metadata['doc_type'] = normalizedDict['details']['deviceproduct']

            try:
                bulk = False
                if options.esbulksize != 0:
                    bulk = True

                res = self.esConnection.save_event(
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
                    message.requeue()
                    return
                except kombu.exceptions.MessageStateError:
                    # state may be already set.
                    return
            except ElasticsearchException as e:
                # exception target for queue capacity issues reported by elastic search so catch the error, report it and retry the message
                try:
                    sys.stderr.write('ElasticSearchException: {0} reported while indexing event'.format(e))
                    message.requeue()
                    return
                except kombu.exceptions.MessageStateError:
                    # state may be already set.
                    return
            # post the dict (kombu serializes it to json) to the events topic queue
            # using the ensure function to shortcut connection/queue drops/stalls, etc.
            # ensurePublish = self.connection.ensure(self.mqproducer, self.mqproducer.publish, max_retries=10)
            # ensurePublish(normalizedDict, exchange=self.topicExchange, routing_key='mozdef.event')
            message.ack()
        except ValueError as e:
            sys.stderr.write("esworker exception in events queue %r\n" % e)


def main():
    # connect and declare the message queue/kombu objects.
    # only py-amqp supports ssl and doesn't recognize amqps
    # so fix up the connection string accordingly
    connString = 'amqp://{0}:{1}@{2}:{3}/{4}'.format(options.mquser, options.mqpassword, options.mqserver, options.mqport, options.mqvhost)
    if options.mqprotocol == 'amqps':
        mqSSL = True
    else:
        mqSSL = False
    mqConn = Connection(connString, ssl=mqSSL)
    # Task Exchange for events sent via http for us to normalize and post to elastic search
    if options.mqack:
        # conservative, store msgs to disk, ack each message
        eventTaskExchange = Exchange(name=options.taskexchange, type='direct', durable=True, delivery_mode=2)
    else:
        # fast, transient delivery, store in memory only, auto-ack messages
        eventTaskExchange = Exchange(name=options.taskexchange, type='direct', durable=True, delivery_mode=1)
    eventTaskExchange(mqConn).declare()
    # Queue for the exchange
    if options.mqack:
        eventTaskQueue = Queue(options.taskexchange, exchange=eventTaskExchange, routing_key=options.taskexchange, durable=True, no_ack=False)
    else:
        eventTaskQueue = Queue(options.taskexchange, exchange=eventTaskExchange, routing_key=options.taskexchange, durable=True, no_ack=True)
    eventTaskQueue(mqConn).declare()

    # topic exchange for anyone who wants to queue and listen for mozdef.event
    eventTopicExchange = Exchange(name=options.eventexchange, type='topic', durable=False, delivery_mode=1)
    eventTopicExchange(mqConn).declare()

    if hasUWSGI:
        sys.stdout.write("started as uwsgi mule {0}\n".format(uwsgi.mule_id()))
    else:
        sys.stdout.write('started without uwsgi\n')
    # consume our queue and publish on the topic exchange
    taskConsumer(mqConn, eventTaskQueue, eventTopicExchange, es).run()


def initConfig():
    #capture the hostname
    options.mozdefhostname = getConfig('mozdefhostname', socket.gethostname(), options.configfile)

    # elastic search options. set esbulksize to a non-zero value to enable bulk posting, set timeout to post no matter how many events after X seconds.
    options.esservers = list(getConfig('esservers', 'http://localhost:9200', options.configfile).split(','))
    options.esbulksize = getConfig('esbulksize', 0, options.configfile)
    options.esbulktimeout = getConfig('esbulktimeout', 30, options.configfile)

    # message queue options
    options.mqserver = getConfig('mqserver', 'localhost', options.configfile)
    options.taskexchange = getConfig('taskexchange', 'eventtask', options.configfile)
    options.eventexchange = getConfig('eventexchange', 'events', options.configfile)
    # how many messages to ask for at once from the message queue
    options.prefetch = getConfig('prefetch', 50, options.configfile)
    options.mquser = getConfig('mquser', 'guest', options.configfile)
    options.mqpassword = getConfig('mqpassword', 'guest', options.configfile)
    options.mqport = getConfig('mqport', 5672, options.configfile)
    options.mqvhost = getConfig('mqvhost', '/', options.configfile)
    # set to either amqp or amqps for ssl
    options.mqprotocol = getConfig('mqprotocol', 'amqp', options.configfile)
    # run with message acking?
    # also toggles transient/persistant delivery (messages in memory only or stored on disk)
    # ack=True sets persistant delivery, False sets transient delivery
    options.mqack = getConfig('mqack', True, options.configfile)

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

    # open ES connection globally so we don't waste time opening it per message
    es = esConnect()

    pluginList = registerPlugins()

    main()
