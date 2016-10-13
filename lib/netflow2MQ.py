#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
# Copyright (c) 2014 Mozilla Corporation
#
# Contributors:
# Jeff Bryner jbryner@mozilla.com
# Anthony Verez netantho@gmail.com

import os
import sys
from configlib import getConfig, OptionParser
import logging
from logging.handlers import SysLogHandler
from datetime import datetime
from datetime import timedelta
from dateutil.parser import parse
import pytz
import re
import json
import time
from collections import deque
from multiprocessing import Process, Queue, JoinableQueue
import random
import errno
import kombu
from kombu import Connection, Queue, Exchange
from Queue import Empty, Full
import socket, struct, sys
from socket import inet_ntoa

SIZE_OF_HEADER = 24
SIZE_OF_RECORD = 48

logger = logging.getLogger(sys.argv[0])

def loggerTimeStamp(self, record, datefmt=None):
    return toUTC(datetime.now()).isoformat()


def initLogger():
    logger.level = logging.INFO
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    formatter.formatTime = loggerTimeStamp
    if options.output == 'syslog':
        logger.addHandler(SysLogHandler(addressess=(options.sysloghostname, options.syslogport), facility=logging.handlers.SysLogHandler.LOG_LOCAL4))
    else:
        sh = logging.StreamHandler(sys.stderr)
        sh.setFormatter(formatter)
        logger.addHandler(sh)


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


def toUTC(suspectedDate, localTimeZone=None):
    '''make a UTC date out of almost anything'''
    utc = pytz.UTC
    objDate = None
    if localTimeZone is None:
        localTimeZone = options.defaultTimeZone
    try:
        if type(suspectedDate) == datetime:
            objDate = suspectedDate
        elif isNumber(suspectedDate):   # epoch?
            objDate = datetime.fromtimestamp(float(suspectedDate))
        elif type(suspectedDate) in (str, unicode):
            objDate = parse(suspectedDate, fuzzy=True)

        if objDate.tzinfo is None:
            objDate = pytz.timezone(localTimeZone).localize(objDate)
            objDate = utc.normalize(objDate)
        else:
            objDate = utc.normalize(objDate)
        if objDate is not None:
            objDate = utc.normalize(objDate)
    except ValueError:
        pass

    return objDate


def postLogs(logcache):
    '''post events to rabbitmq
       expects a queue object from the multiprocessing library
       looks for a list of servers in options.mqservers separated by commas
       creates connections to each, initializes an exchange
       and a producer
       and randomly chooses one to publish incoming messages to.
    '''
    mqproducers = list()
    canQuit = False
    logger.info('starting message queue posting process')
    # connect and declare the message queue/kombu objects.
    # with a list of producers for every potential message queue server.

    for server in options.mqservers.split(','):
        connString = 'amqp://{0}:{1}@{2}:{3}//'.format(options.mquser, options.mqpassword, server, options.mqport)
        mqConn = Connection(connString)
        eventTaskExchange = Exchange(name=options.taskexchange, type='direct', durable=True)
        eventTaskExchange(mqConn).declare()
        mqproducer = mqConn.Producer(serializer='json')
        ensurePublish = mqConn.ensure(mqproducer, mqproducer.publish, max_retries=10)
        mqproducers.append(ensurePublish)

    while True:
        try:
            # see if we have anything to post
            # waiting a bit to not end until we are told we can stop.
            postdata = logcache.get(True, 1)
            if postdata is None:
                # signalled from parent process that it's ok to stop.
                logcache.task_done()
                canQuit = True

            elif len(postdata) > 0:
                # post to eventtask exchange
                try:
                    publisher = random.choice(mqproducers)
                    publisher(postdata, exchange=eventTaskExchange, routing_key=options.taskexchange)
                except Exception as e:
                    logger.error('Exception while posting message: %r' % e)
                logcache.task_done()
        except Empty as e:
            if canQuit:
                logger.info('shutting down message queue publisher')
                break

    logger.info('{0} done'.format('log posting task'))


def main():
    # create a list of logs we can append json to and call for a post when we want.
    logcache = Queue()

    logger.info('started')
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(('0.0.0.0', int(options.netflowport)))
    # start a process to post our stuff.
    logcache = JoinableQueue()
    postingProcess = Process(target=postLogs, args=(logcache,), name="netflow2MozdefMQPost")
    postingProcess.start()

    while True:
        try:
            buf, address = sock.recvfrom(1500)
            netflowsource=address[0]
            netflowsource=socket.getfqdn(netflowsource)
            
            #is the sender in a whitelist of accepted senders?
            if len(options.senderwhitelist) > 0:
                if netflowsource not in options.senderwhitelist.split(','):
                    logger.debug('ignoring: {0}'.format(netflowsource))
                    continue
            

            header = {}
            # NetFlow export format version number
            # Number of flows exported in this packet (1-30)
            (header['version'], header['count']) = struct.unpack('!HH',buf[0:4])
            if header['version'] != 5:
                logger.error( "Not NetFlow v5!")
                continue
            
            # It's pretty unlikely you'll ever see more then 1000 records in a 1500 byte UDP packet
            if header['count'] <= 0 or header['count'] >= 1000:
                logger.error("Invalid count %s" % header['count'])
                continue
            
            # Current time in milliseconds since the export device booted
            header['uptime'] = socket.ntohl(struct.unpack('I', buf[4:8])[0])
            # Current count of seconds since 0000 UTC 1970
            header['unixseconds'] = socket.ntohl(struct.unpack('I', buf[8:12])[0])
            # Residual nanoseconds since 0000 UTC 1970
            header['unixnanoseconds'] = socket.ntohl(struct.unpack('I', buf[12:16])[0])
            # Sequence counter of total flows seen
            header['flowsequence'] = socket.ntohl(struct.unpack('I', buf[16:20])[0])
            # Type of flow-switching engine
            header['enginetype'] = socket.ntohl(struct.unpack('B', buf[20])[0])
            # Slot number of the flow-switching engine
            header['engineid'] = socket.ntohl(struct.unpack('B', buf[21])[0])
            # First two bits hold the sampling mode; remaining 14 bits hold value of sampling interval
            header['samplinginterval'] = struct.unpack('!H', buf[22:24])[0] & 0b0011111111111111

            
            for i in range(0, header['count']):
                try:
                    base = SIZE_OF_HEADER+(i*SIZE_OF_RECORD)
            
                    data = struct.unpack('!IIIIHH',buf[base+16:base+36])
                    data2 = struct.unpack('!BBBHHBB',buf[base+37:base+46])
            
                    record = header
                    # Netflow source
                    record['hostname'] = netflowsource
                    # Source IP addressess
                    record['sourceipaddress'] = inet_ntoa(buf[base+0:base+4])
                    # Destination IP addressess
                    record['destinationipaddress'] = inet_ntoa(buf[base+4:base+8])
                    # IP addressess of next hop router
                    record['nexthop'] = inet_ntoa(buf[base+8:base+12])
                    # Packets in the flow
                    record['packets'] = data[0]
                    # Total number of Layer 3 bytes in the packets of the flow
                    record['octets'] = data[1]
                    # SysUptime at start of flow
                    record['first'] = data[2]
                    # SysUptime at the time the last packet of the flow was received
                    record['last'] = data[3]
                    # TCP/UDP source port number or equivalent
                    record['sourceport'] = data[4]
                    # TCP/UDP destination port number or equivalent
                    record['destinationport'] = data[5]
                    # Cumulative OR of TCP flags
                    record['tcpflags'] = data2[0]
                    # IP protocol type (for example, TCP = 6; UDP = 17)
                    record['protocol'] = data2[1]
                    # IP type of service (ToS)
                    record['tos'] = data2[2]
                    # Autonomous system number of the source, either origin or peer
                    record['sourceasn'] = data2[3]
                    # Autonomous system number of the destination, either origin or peer
                    record['destinationasn'] = data2[4]
                    # Source addressess prefix mask bits
                    record['sourcemask'] = data2[5]
                    # Destination addressess prefix mask bits
                    record['destinationmask'] = data2[6]
            
                    #publish record
                    if str(record['sourceport']) not in options.sourceportignore.split(','):
                    
                        nfevent = dict(utctimestamp=toUTC(datetime.now()).isoformat())
                        nfevent['tags'] = ['netflow', 'network']
                        nfevent['category'] = 'netflow'
                        nfevent['summary'] = '{0}:{1} --> {2}:{3}'.format(record['sourceipaddress'], record['sourceport'], record['destinationipaddress'], record['destinationport'])
                        nfevent['details'] = record
                        logcache.put(json.dumps(nfevent))
                        logger.debug(json.dumps(nfevent))
                except Exception as e:
                    logger.error('%r'%e)
                    continue


        except KeyboardInterrupt:
            sys.exit(1)
        except ValueError as e:
            logger.fatal('Exception while handling netflow message: %r' % e)
            sys.exit(1)
    logger.info('finished')


def initConfig():
    # output our log to stdout or syslog
    options.output = getConfig('output', 'stdout', options.configfile)
    options.sysloghostname = getConfig('sysloghostname', 'localhost', options.configfile)
    options.syslogport = getConfig('syslogport', 514, options.configfile)
    options.logfile = getConfig('logfile', 'auditd.mozdef.fifo', options.configfile)

    # change this to your default zone for when it's not specified
    options.defaultTimeZone = getConfig('defaulttimezone', 'US/Pacific', options.configfile)

    # mq server/exchange options.
    # mqservers can be a comma delimited list of server,server2,server3 etc to load balance the posts.
    options.mqservers = getConfig('mqservers', 'localhost', options.configfile)
    options.taskexchange = getConfig('taskexchange', 'eventtask', options.configfile)
    options.mquser = getConfig('mquser', 'guest', options.configfile)
    options.mqpassword = getConfig('mqpassword', 'guest', options.configfile)
    options.mqport = getConfig('mqport', 5672, options.configfile)
    
    #netflow options
    options.netflowport = getConfig('netflowport', 2056, options.configfile)
    #comma separated list of ports to ignore/drop
    #to avoid capturing return traffic
    options.sourceportignore = getConfig('sourceportignore', '', options.configfile)
    #to avoid capturing traffic from unwanted netflow senders
    options.senderwhitelist = getConfig('senderwhitelist', '', options.configfile)


if __name__ == '__main__':
    parser = OptionParser()
    parser.add_option("-c", dest='configfile', default=sys.argv[0].replace('.py', '.conf'), help="configuration file to use")
    (options, args) = parser.parse_args()
    initConfig()
    initLogger()
    main()
