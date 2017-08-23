#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
# Copyright (c) 2014 Mozilla Corporation
#
# Contributors:
# Jeff Bryner jbryner@mozilla.com

# kombu's support for SQS is buggy
# so this version uses boto
# to read an SQS queue and put events into elastic search
# in the same manner as esworker.py


import json
import math
import os
import pynsive
import sys
import socket
import time
from configlib import getConfig, OptionParser
from datetime import datetime, timedelta
from operator import itemgetter
import boto.sqs
from boto.sqs.message import RawMessage
import base64
import kombu

import sys
import os
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../lib'))
from utilities.toUTC import toUTC
from elasticsearch_client import ElasticsearchClient, ElasticsearchBadServer, ElasticsearchInvalidIndex, ElasticsearchException

# running under uwsgi?
try:
    import uwsgi
    hasUWSGI = True
except ImportError as e:
    hasUWSGI = False


def removeAt(astring):
    '''remove the leading @ from a string'''
    return astring.replace('@', '')


def isCEF(aDict):
    # determine if this is a CEF event
    # could be an event posted to the /cef http endpoint
    if 'endpoint' in aDict.keys() and aDict['endpoint'] == 'cef':
        return True
    # maybe it snuck in some other way
    # check some key CEF indicators (the header fields)
    if 'fields' in aDict.keys() and isinstance(aDict['fields'], dict):
        lowerKeys = [s.lower() for s in aDict['fields'].keys()]
        if 'devicevendor' in lowerKeys and 'deviceproduct' in lowerKeys and 'deviceversion' in lowerKeys:
            return True
    if 'details' in aDict.keys() and isinstance(aDict['details'], dict):
        lowerKeys = [s.lower() for s in aDict['details'].keys()]
        if 'devicevendor' in lowerKeys and 'deviceproduct' in lowerKeys and 'deviceversion' in lowerKeys:
            return True
    return False


def toUnicode(obj, encoding='utf-8'):
    if type(obj) in [int, long, float, complex]:
        # likely a number, convert it to string to get to unicode
        obj = str(obj)
    if isinstance(obj, basestring):
        if not isinstance(obj, unicode):
            obj = unicode(obj, encoding)
    return obj


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

            if k in ('message', 'summary'):
                returndict[u'summary'] = toUnicode(v)

            if k in ('payload') and 'summary' not in aDict.keys():
                # special case for heka if it sends payload as well as a summary, keep both but move payload to the details section.
                returndict[u'summary'] = toUnicode(v)
            elif k in ('payload'):
                if 'details' not in returndict.keys():
                    returndict[u'details'] = dict()
                returndict[u'details']['payload'] = toUnicode(v)

            if k in ('eventtime', 'timestamp', 'utctimestamp'):
                returndict[u'utctimestamp'] = toUTC(v).isoformat()
                returndict[u'timestamp'] = toUTC(v).isoformat()

            if k in ('hostname', 'source_host', 'host'):
                returndict[u'hostname'] = toUnicode(v)

            if k in ('tags'):
                if len(v) > 0:
                    returndict[u'tags'] = v

            # nxlog keeps the severity name in syslogseverity,everyone else should use severity or level.
            if k in ('syslogseverity', 'severity', 'severityvalue', 'level'):
                returndict[u'severity'] = toUnicode(v).upper()

            if k in ('facility', 'syslogfacility'):
                returndict[u'facility'] = toUnicode(v)

            if k in ('pid', 'processid'):
                returndict[u'processid'] = toUnicode(v)

            # nxlog sets sourcename to the processname (i.e. sshd), everyone else should call it process name or pname
            if k in ('pname', 'processname', 'sourcename'):
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
        sys.stderr.write(
            'esworker.sqs exception normalizing the message %r\n' % e)
        return None

    return returndict


def esConnect():
    '''open or re-open a connection to elastic search'''
    return ElasticsearchClient((list('{0}'.format(s) for s in options.esservers)), options.esbulksize)


class taskConsumer(object):

    def __init__(self, mqConnection, taskQueue,  esConnection):
        self.connection = mqConnection
        self.esConnection = esConnection
        self.taskQueue = taskQueue

        if options.esbulksize != 0:
            # if we are bulk posting enable a timer to occasionally flush the bulker even if it's not full
            # to prevent events from sticking around an idle worker
            self.esConnection.start_bulk_timer()

    def run(self):
        # Boto expects base64 encoded messages - but if the writer is not boto it's not necessarily base64 encoded
        # Thus we've to detect that and decode or not decode accordingly
        self.taskQueue.set_message_class(RawMessage)
        while True:
            try:
                records=self.taskQueue.get_messages(options.prefetch)  #10 max
                for msg in records:
                    # msg.id is the id,
                    # get_body() should be json

                    # pre process the message a bit
                    tmp = msg.get_body()
                    try:
                        msgbody = json.loads(tmp)
                    except ValueError:
                        # If Boto wrote to the queue, it might be base64 encoded, so let's decode that
                        try:
                            tmp = base64.b64decode(tmp)
                            msgbody = json.loads(tmp)
                        except:
                            sys.stdout.write('invalid message, not JSON <dropping message and continuing>: %r\n' % msg.get_body())
                            self.taskQueue.delete_message(msg)
                            continue

                    event = dict()
                    event = msgbody

                    # Was this message sent by fluentd-sqs
                    fluentd_sqs_specific_fields = {
                        'az', 'instance_id', '__tag'}
                    if fluentd_sqs_specific_fields.issubset(
                            set(msgbody.keys())):
                        # Until we can influence fluentd-sqs to set the
                        # 'customendpoint' key before submitting to SQS, we'll
                        # need to do it here
                        # TODO : Change nubis fluentd output to include
                        # 'customendpoint'
                        event['customendpoint'] = True

                    if 'tags' in event:
                        event['tags'].extend([options.taskexchange])
                    else:
                        event['tags'] = [options.taskexchange]

                    #process message
                    self.on_message(event, msg)

                    #delete message from queue
                    self.taskQueue.delete_message(msg)
                time.sleep(.1)

            except KeyboardInterrupt:
                sys.exit(1)
            except ValueError as e:
                sys.stdout.write('Exception while handling message: %r'%e)
                sys.exit(1)

    def on_message(self, body, message):
        #print("RECEIVED MESSAGE: %r" % (body, ))
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
                    sys.stderr.write(
                        "esworker.sqs exception: unknown body type received "
                        "%r\n" % body)
                    #message.ack()
                    return
            else:
                sys.stderr.write(
                    "esworker.sqs exception: unknown body type received "
                    "%r\n" % body)
                #message.ack()
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
                #message.ack()
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

                res = self.esConnection.save_object(
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
                    #message.requeue()
                    return
                except kombu.exceptions.MessageStateError:
                    # state may be already set.
                    return
            except ElasticsearchException as e:
                # exception target for queue capacity issues reported by elastic search so catch the error, report it and retry the message
                try:
                    sys.stderr.write('ElasticSearchException: {0} reported while indexing event'.format(e))
                    #message.requeue()
                    return
                except kombu.exceptions.MessageStateError:
                    # state may be already set.
                    return

            #message.ack()
        except ValueError as e:
            sys.stderr.write(
                "esworker.sqs exception in events queue %r\n" % e)


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
            elif isinstance(v,dict):
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
        sys.stdout.write('Can only process SQS queues, terminating\n');
        sys.exit(1)

    mqConn = boto.sqs.connect_to_region(options.region,
                                      aws_access_key_id=options.accesskey,
                                      aws_secret_access_key=options.secretkey)
    # attach to the queue
    eventTaskQueue = mqConn.get_queue(options.taskexchange)

    # consume our queue
    taskConsumer(mqConn, eventTaskQueue, es).run()


def initConfig():
    #capture the hostname
    options.mozdefhostname = getConfig('mozdefhostname', socket.gethostname(), options.configfile)

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


if __name__ == '__main__':
    # configure ourselves
    parser = OptionParser()
    parser.add_option("-c", dest='configfile', default=sys.argv[0].replace('.py', '.conf'), help="configuration file to use")
    (options, args) = parser.parse_args()
    initConfig()

    # open ES connection globally so we don't waste time opening it per message
    es = esConnect()

    # force a check for plugins and establish the plugin list
    pluginList = list()
    lastPluginCheck = datetime.now()-timedelta(minutes=60)
    pluginList, lastPluginCheck = checkPlugins(pluginList, lastPluginCheck)

    main()
