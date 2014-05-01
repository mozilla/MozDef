#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
# Copyright (c) 2014 Mozilla Corporation
#
# Contributors:
# Jeff Bryner jbryner@mozilla.com
# Anthony Verez averez@mozilla.com

# Faster than json http://blog.yjl.im/2011/02/simple-simplejson-parse-time-test.html
import simplejson as json
import kombu
import math
import os
import pyes
import pytz
import pynsive
import re
import sys
import time
from configlib import getConfig, OptionParser
from datetime import datetime, timedelta
from dateutil.parser import parse
from operator import itemgetter
from kombu import Connection, Queue, Exchange
from kombu.mixins import ConsumerMixin
from threading import Timer

# running under uwsgi?
try:
    import uwsgi
    hasUWSGI = True
except ImportError as e:
    hasUWSGI = False


def isNumber(s):
    'check if a token is numeric, return bool'
    try:
        float(s)  # for int, long and float
    except ValueError:
        try:
            complex(s)  # for complex
        except ValueError:
            return False
    return True


def digits(n):
    '''return the number of digits in a number'''
    if n > 0:
        digits = int(math.log10(n))+1
    elif n == 0:
        digits = 1
    else:
        digits = int(math.log10(-n))+2
    return digits


def toUTC(suspectedDate, localTimeZone=None):
    '''make a UTC date out of almost anything'''
    utc = pytz.UTC
    objDate = None
    if localTimeZone is None:
        localTimeZone = options.defaultTimeZone

    if type(suspectedDate) == datetime:
        objDate = suspectedDate
    elif isNumber(suspectedDate):
        # epoch? but seconds/milliseconds/nanoseconds (lookin at you heka)
        epochDivisor = int(str(1) + '0'*(digits(suspectedDate) % 10))
        objDate = datetime.fromtimestamp(float(suspectedDate/epochDivisor))
    elif type(suspectedDate) in (str, unicode):
        objDate = parse(suspectedDate, fuzzy=True)

    if objDate.tzinfo is None:
        objDate = pytz.timezone(localTimeZone).localize(objDate)
        objDate = utc.normalize(objDate)
    else:
        objDate = utc.normalize(objDate)
    if objDate is not None:
        objDate = utc.normalize(objDate)

    return objDate.isoformat()


def removeDictAt(aDict):
    '''remove the @ symbol from any field/key names'''
    returndict = dict()
    for k, v in aDict.iteritems():
        k = k.replace('@', '')
        returndict[k] = v
    return returndict


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


def safeString(aString):
    '''return a safe string given a potentially unsafe, unicode, etc'''
    returnString = ''
    if isinstance(aString, str):
        returnString = aString
    if isinstance(aString, unicode):
        returnString = aString.encode('ascii', 'ignore')
    return returnString


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

    # save the source event for chain of custody/forensics
    # returndict['original']=aDict

    if 'utctimestamp' not in returndict.keys():
        # default in case we don't find a reasonable timestamp
        returndict['utctimestamp'] = toUTC(datetime.now())

    # set the timestamp when we received it, i.e. now
    returndict['receivedtimestamp'] = toUTC(datetime.now())
    try:
        for k, v in aDict.iteritems():
            normalisedKey = removeAt(k.lower())

            if normalisedKey in ('message', 'summary'):
                returndict[u'summary'] = toUnicode(v)

            if normalisedKey in ('payload') and 'summary' not in aDict.keys():
                # special case for heka if it sends payload as well as a summary, keep both but move payload to the details section.
                returndict[u'summary'] = toUnicode(v)
            elif normalisedKey in ('payload'):
                if 'details' not in returndict.keys():
                    returndict[u'details'] = dict()
                returndict[u'details']['payload'] = toUnicode(v)

            if normalisedKey in ('eventtime', 'timestamp'):
                returndict[u'utctimestamp'] = toUTC(v)
                returndict[u'timestamp'] = toUTC(v)

            if normalisedKey in ('hostname', 'source_host', 'host'):
                returndict[u'hostname'] = toUnicode(v)

            if normalisedKey in ('tags'):
                if len(v) > 0:
                    returndict[u'tags'] = v

            # nxlog keeps the severity name in syslogseverity,everyone else should use severity or level.
            if normalisedKey in ('syslogseverity', 'severity', 'severityvalue', 'level'):
                returndict[u'severity'] = toUnicode(v).upper()

            if normalisedKey in ('facility', 'syslogfacility'):
                returndict[u'facility'] = toUnicode(v)

            if normalisedKey in ('pid', 'processid'):
                returndict[u'processid'] = toUnicode(v)

            # nxlog sets sourcename to the processname (i.e. sshd), everyone else should call it process name or pname
            if normalisedKey in ('pname', 'processname', 'sourcename'):
                returndict[u'processname'] = toUnicode(v)

            # the file, or source
            if normalisedKey in ('path', 'logger', 'file'):
                returndict[u'eventsource'] = toUnicode(v)

            if normalisedKey in ('type', 'eventtype', 'category'):
                returndict[u'category'] = toUnicode(v)

            # custom fields as a list/array
            if normalisedKey in ('fields', 'details'):
                if len(v) > 0:
                    returndict[u'details'] = v

            # custom fields/details as a one off, not in an array
            # i.e. fields.something=value or details.something=value
            # move them to a dict for consistency in querying
            if normalisedKey.startswith('fields.') or normalisedKey.startswith('details.'):
                newName = k.lower().replace('fields.', '')
                newName = newName.lower().replace('details.', '')
                # add a dict to hold the details if it doesn't exist
                if 'details' not in returndict.keys():
                    returndict[u'details'] = dict()
                # add field
                returndict[u'details'][unicode(newName)] = toUnicode(v)
    except Exception as e:
        sys.stderr.write('esworker exception normalizing the message %r\n' % e)
        return None

    return returndict


def esConnect(conn):
    '''open or re-open a connection to elastic search'''
    return pyes.ES(server=(list('{0}'.format(s) for s in options.esservers)), bulk_size=options.esbulksize)


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
            # if we are bulk posting enable a timer to occasionally flush the pyes bulker even if it's not full
            # to prevent events from sticking around an idle worker
            Timer(options.esbulktimeout, self.flush_es_bulk).start()

    def get_consumers(self, Consumer, channel):
        consumer = Consumer(self.taskQueue, callbacks=[self.on_message], accept=['json', 'text/plain'])
        consumer.qos(prefetch_count=options.prefetch)
        return [consumer]

    def flush_es_bulk(self):
        '''if we are bulk posting to elastic search force a bulk post even if we don't have
           enough items to trigger a post normally.
           This allows you to have lots of workers and not wait for events for too long if
           there isn't a steady event stream while still retaining the throughput capacity
           that bulk processing affords.
        '''
        # sys.stderr.write('mule {0} flushing bulk elastic search posts\n'.format(self.muleid))
        self.esConnection.flush_bulk(True)
        Timer(options.esbulktimeout, self.flush_es_bulk).start()

    def on_message(self, body, message):
        # print("RECEIVED MESSAGE: %r" % (body, ))
        try:
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
            # normalize the dict
            normalizedDict = keyMapping(bodyDict)

            # send the dict to elastic search and to the events task queue
            if normalizedDict is not None and isinstance(normalizedDict, dict) and normalizedDict.keys():
                # could be empty,or invalid
                # pass the event to any plug-ins we have registered
                # disable periodic checking for new plugins
                # because of memory leak
                # checkPlugins(pluginList,lastPluginCheck)
                sendEventToPlugins(normalizedDict, pluginList)

                # make a json version for posting to elastic search
                jbody = json.JSONEncoder().encode(normalizedDict)

                # figure out what type of document we are indexing and post to the elastic search index.
                doctype = 'event'
                if isCEF(bodyDict):
                    # cef records are set to the 'deviceproduct' field value.
                    doctype = 'cef'
                    if 'fields' in bodyDict.keys() and 'deviceproduct' in bodyDict['fields'].keys():
                        # don't create strange doc types..
                        if ' ' not in bodyDict['fields']['deviceproduct'] and '.' not in bodyDict['fields']['deviceproduct']:
                            doctype = bodyDict['fields']['deviceproduct']
                    if 'details' in bodyDict.keys() and 'deviceproduct' in bodyDict['details'].keys():
                        # don't create strange doc types..
                        if ' ' not in bodyDict['details']['deviceproduct'] and '.' not in bodyDict['details']['deviceproduct']:
                            doctype = bodyDict['details']['deviceproduct']

                try:
                    if options.esbulksize != 0:
                        res = self.esConnection.index(index='events', doc_type=doctype, doc=jbody, bulk=True)
                    else:
                        res = self.esConnection.index(index='events', doc_type=doctype, doc=jbody, bulk=False)

                except (pyes.exceptions.NoServerAvailable, pyes.exceptions.InvalidIndexNameException) as e:
                    # handle loss of server or race condition with index rotation/creation/aliasing
                    try:
                        self.esConnection = esConnect(None)
                        message.requeue()
                        return
                    except kombu.exceptions.MessageStateError:
                        # state may be already set.
                        return
                except pyes.exceptions.ElasticSearchException as e:
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
                ensurePublish = self.connection.ensure(self.mqproducer, self.mqproducer.publish, max_retries=10)
                ensurePublish(normalizedDict, exchange=self.topicExchange, routing_key='mozdef.event')
            message.ack()
        except ValueError as e:
            sys.stderr.write("esworker exception in events queue %r\n" % e)


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
                    if isinstance(mreg, dict):
                        print('[*] plugin {0} registered to receive messages with {1}'.format(mname, mreg))
                    if isinstance(mreg, type(re.compile(''))):
                        print('[*] plugin {0} registered with a regex: {1}'.format(mname, mreg.pattern))
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


def flattenDict(inDict, pre=None, values=True):
    '''given a dictionary, potentially with multiple sub dictionaries
       return a period delimited version of the dict with or without values
       i.e. {'something':'value'} becomes something=value
            {'something':{'else':'value'}} becomes something.else=value
    '''
    pre = pre[:] if pre else []
    if isinstance(inDict, dict):
        for key, value in inDict.iteritems():
            if isinstance(value, dict):
                for d in flattenDict(value, pre + [key], values):
                    yield d
            else:
                if pre:
                    if values:
                        if isinstance(value, str):
                            yield '.'.join(pre) + '.' + key + '=' + str(value)
                        elif isinstance(value, unicode):
                            yield '.'.join(pre) + '.' + key + '=' + value.encode('ascii', 'ignore')
                        elif value is None:
                            yield '.'.join(pre) + '.' + key + '=None'
                    else:
                        yield '.'.join(pre) + '.' + key
                else:
                    if values:
                        if isinstance(value, str):
                            yield key + '=' + str(value)
                        elif isinstance(value, unicode):
                            yield key + '=' + value.encode('ascii', 'ignore')
                        elif value is None:
                            yield key + '=None'
                    else:
                        yield key
    else:
        yield '-'.join(pre) + '.' + inDict


def sendEventToPlugins(anevent, pluginList):
    '''compare the event to the plugin registrations.
       plugins register with a dictionary either including a value or None
       None meaning send anything with that field.
       Value meaning send anything mathing that exact value
       Do this comparison by flattening the dict into key.key.key=value being mindful of sub dictionaries
    '''
    if not isinstance(anevent, dict):
        raise TypeError('event is type {0}, should be a dict'.format(type(anevent)))
    # expecting tuple of module,criteria,priority in pluginList

    eventWithValues = [e for e in flattenDict(anevent)]
    eventWithoutValues = [e for e in flattenDict(anevent, values=False)]
    # sort the plugin list by priority
    regexnull = re.compile('')
    for plugin in sorted(pluginList, key=itemgetter(2), reverse=False):
        # assume we don't run this event through the plugin
        send = False
        # regex or dict as a registration
        # no regex instance type to compare to..so compare to re.compile
        if isinstance(plugin[1], type(regexnull)):
            for e in eventWithValues:
                if plugin[1].search(e):
                    send = True
        if isinstance(plugin[1], dict):
            # list of the plugin field requests. Will return key=None for keys registered without a particular value
            pluginRegistration = flattenDict(plugin[1]).keys()
            # print('plug in wants: {0}'.format(pluginRegistration))
            for p in pluginRegistration:
                if p.endswith('=None'):  # a request for a field, no specific value
                    if p.replace('=None', '') in eventWithoutValues:
                        send = True
                else:
                    if p in eventWithValues:
                        send = True
        if send:
            anevent = plugin[0].onMessage(anevent)
            eventWithValues = [e for e in flattenDict(anevent)]
            eventWithoutValues = [e for e in flattenDict(anevent, values=False)]

    return anevent


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
    eventTaskExchange = Exchange(name=options.taskexchange, type='direct', durable=True)
    eventTaskExchange(mqConn).declare()
    # Queue for the exchange
    eventTaskQueue = Queue(options.taskexchange, exchange=eventTaskExchange, routing_key=options.taskexchange)
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
    # change this to your default zone for when it's not specified
    options.defaultTimeZone = getConfig('defaulttimezone', 'US/Pacific', options.configfile)

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
    es = esConnect(None)

    # force a check for plugins and establish the plugin list
    pluginList = list()
    lastPluginCheck = datetime.now()-timedelta(minutes=60)
    pluginList, lastPluginCheck = checkPlugins(pluginList, lastPluginCheck)

    main()
