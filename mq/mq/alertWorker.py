#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
# Copyright (c) 2014 Mozilla Corporation
#
# Contributors:
# Jeff Bryner jbryner@mozilla.com

import datetime
import dateutil.parser
import json
import kombu
import logging
import pyes
import re
import sys
from configlib import getConfig, OptionParser
from kombu import Connection, Queue, Exchange
from kombu.mixins import ConsumerMixin
from logging.handlers import SysLogHandler

logger = logging.getLogger()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')


def isTimeToken(token):
    info = dateutil.parser.parser().info
    if any(f(token) for f in (info.jump, info.weekday, info.month, info.hms,
                              info.ampm, info.pertain, info.utczone,
                              info.tzoffset)):
        return True
    try:
        float(token)
        return True
    except ValueError:
        pass
    try:
        if type(dateutil.parser.parse(token)) == datetime.datetime:
            return True
    except Exception as e:
        return False
    return False


def splitTime(inString):
    '''separate a string into anything that is not a date/time token
       and anything that could be a time token
       useful for parsing incoming syslog to move
       timestamps into a separate field.
    '''
    outString = []
    outTime = []
    for i in inString.split():
        if isTimeToken(i):
            outTime.append(i)
        else:
            outString.append(i)
    return(' '.join(outString), ' '.join(outTime))


def esConnect(conn):
    '''open or re-open a connection to elastic search'''
    if isinstance(conn, pyes.es.ES):
        return pyes.ES((list('{0}'.format(s) for s in options.esservers)))
    else:
        return pyes.ES((list('{0}'.format(s) for s in options.esservers)))


class eventConsumer(ConsumerMixin):

    '''read in events,
       compare them to things we've been asked to alert on and
       publish to the alerts queue and elastic search'''

    def __init__(self, mqEventsConnection, eventQueue, mqAlertsConnection, alertExchange, esConnection):
        self.eventsConnection = mqEventsConnection
        self.connection = mqEventsConnection  # default connection for the kombu mixin
        self.esConnection = esConnection
        self.alertsConnection = mqAlertsConnection
        self.eventQueue = eventQueue
        self.alertExchange = alertExchange
        self.mqAlertsProducer = self.alertsConnection.Producer(serializer='json')

    def get_consumers(self, Consumer, channel):
        consumer = Consumer(
            self.eventQueue,
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
                    logger.exception(
                        "alertworker exception: unknown body type received %r" % body)
                    return
            else:
                logger.exception(
                    "alertworker exception: unknown body type received %r" % body)
                return

            for rex in options.regexlist:
                if 'tag' in rex.keys():
                    # we've been asked to limit scope to mq items with this tag
                    if 'tags' not in bodyDict.keys():
                        # no tags to compare
                        return
                    if 'tags' in bodyDict.keys() and rex['tag'] not in bodyDict['tags']:
                        # tags..but not one matching.
                        return
                if 'summary' in bodyDict.keys() and re.findall(rex['expression'], bodyDict['summary']):
                    if 'severity' in rex.keys():
                        bodyDict['severity'] = rex['severity']
                    if 'category' in rex.keys():
                        bodyDict['category'] = rex['category']
                    if options.removemessagedate:
                        msg, adate = splitTime(bodyDict['summary'])
                        bodyDict['summary'] = msg
                    try:
                        self.esConnection.index(index='alerts',
                                                doc_type='alert',
                                                doc=bodyDict)
                    except (pyes.exceptions.NoServerAvailable,
                            pyes.exceptions.InvalidIndexNameException) as e:
                        # handle loss of server or race condition with index
                        # rotation/creation/aliasing
                        try:
                            self.esConnection = esConnect(None)
                            message.requeue()
                            return
                        except kombu.exceptions.MessageStateError:
                            # state may be already set.
                            return
                    # post the dict (kombu serializes it to json) to the
                    # alerts topic queue using the ensure function to
                    # shortcut connection/queue drops/stalls, etc.
                    ensurePublish = self.alertsConnection.ensure(
                        self.mqAlertsProducer,
                        self.mqAlertsProducer.publish,
                        max_retries=10)
                    ensurePublish(
                        bodyDict,
                        exchange=self.alertExchange,
                        routing_key='mozdef.alert')
                    message.ack()
                    break  # only publish once on the first regex hit
        except ValueError as e:
            logger.exception(
                "alertworker exception while processing events queue %r" % e)


def main():
    if options.output == 'syslog':
        logger.addHandler(
            SysLogHandler(address=(options.sysloghostname, options.syslogport)))
    else:
        sh = logging.StreamHandler(sys.stderr)
        sh.setFormatter(formatter)
        logger.addHandler(sh)

    # connect and declare the message queue/kombu objects.
    # Event server/exchange/queue
    eventConnString = 'amqp://{0}:{1}@{2}:{3}//'.format(options.mquser,
                                                        options.mqpassword,
                                                        options.mqeventserver,
                                                        options.mqport)
    mqEventConn = Connection(eventConnString)

    # Exchange for events we inspect to regex into an alert.
    eventExchange = Exchange(name=options.eventexchange,
                             type='topic',
                             durable=False,
                             delivery_mode=1)
    eventExchange(mqEventConn).declare()
    # Queue for the exchange
    eventQueue = Queue(options.eventexchange,
                       exchange=eventExchange,
                       routing_key=options.eventqueue,
                       durable=False,
                       no_ack=True)
    eventQueue(mqEventConn).declare()

    # alert server/exchange
    alertConnString = 'amqp://{0}:{1}@{2}:{3}//'.format(options.mquser,
                                                        options.mqpassword,
                                                        options.mqalertserver,
                                                        options.mqport)
    mqAlertConn = Connection(alertConnString)

    # topic exchange to send alerts to
    alertExchange = Exchange(
        name=options.alertexchange,
        type='topic',
        durable=False,
        delivery_mode=1)
    alertExchange(mqAlertConn).declare()

    # consume our events, publish alerts.
    eventConsumer(mqEventConn, eventQueue, mqAlertConn, alertExchange, es).run()


def initConfig():
    '''setup the default options and override with any in our .conf file'''
    # message queue server hostname to listen to for events
    options.mqeventserver = getConfig(
        'mqeventserver',
        'localhost',
        options.configfile)
    # message queue server hostname to send alerts to (in case it's different)
    options.mqalertserver = getConfig(
        'mqalertserver',
        'localhost',
        options.configfile)
    # event queue topic
    options.eventqueue = getConfig(
        'eventqueue',
        'mozdef.event',
        options.configfile)
    # event queue exchange name
    options.eventexchange = getConfig(
        'eventexchange',
        'events',
        options.configfile)
    # alert queue topic
    options.alertqueue = getConfig(
        'alertqueue',
        'mozdef.alert',
        options.configfile)
    # alert queue exchange name
    options.alertexchange = getConfig(
        'alertexchange',
        'alerts',
        options.configfile)
    # how many messages to ask for at once
    options.prefetch = getConfig('prefetch', 50, options.configfile)
    options.mquser = getConfig('mquser', 'guest', options.configfile)
    options.mqpassword = getConfig('mqpassword', 'guest', options.configfile)
    options.mqport = getConfig('mqport', 5672, options.configfile)

    # output our log to stdout or syslog
    options.output = getConfig('output', 'stdout', options.configfile)
    options.sysloghostname = getConfig(
        'sysloghostname', 'localhost', options.configfile)  # syslog hostname
    options.syslogport = getConfig(
        'syslogport', 514, options.configfile)  # syslog port
    # do we remove any date string from the 'summary' field (removes syslog
    # timestamps)
    options.removemessagedate = getConfig(
        'removemessagedate', True, options.configfile)
    options.esservers = list(
        getConfig('esservers',
                  'http://localhost:9200',
                  options.configfile).split(','))

    # load any alert regexes from the config file
    # expecting one line, tab delimited json:
    # regexes={"type":"LDAP Group Update","expression":"ou=groups","severity":"INFO"}   {"type":"LDAP Delete","expression":"delete","severity":"INFO"}
    # adding a tag attribute will limit expression matching to items with that tag
    # regexes={"type":"LDAP Group Update","expression":"ou=groups","severity":"INFO","tag":"ldap"}
    regexes = getConfig('regexes', '', options.configfile)
    options.regexlist = []
    if len(regexes) > 0:
        for r in regexes.split('\t'):
            options.regexlist.append(json.loads(r))

if __name__ == '__main__':
    parser = OptionParser()
    parser.add_option("-c",
                      dest='configfile',
                      default=sys.argv[0].replace('.py', '.conf'),
                      help="configuration file to use")
    (options, args) = parser.parse_args()
    initConfig()
    es = esConnect(None)
    main()
