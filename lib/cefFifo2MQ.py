#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
# Copyright (c) 2014 Mozilla Corporation
#
# Contributors:
# Jeff Bryner jbryner@mozilla.com
# Guillaume Destuynder gdestuynder@mozilla.com

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
from os.path import exists
import time
from collections import deque
import fcntl
from multiprocessing import Process, Queue, JoinableQueue
import random
import errno
import select
import kombu
from kombu import Connection, Queue, Exchange
from Queue import Empty, Full

logger = logging.getLogger(sys.argv[0])
# sample CEF record:
# CEF:0|Unix|auditd|1|CHMOD|CHMOD failed|3|end=1391190619 fname="/var/log/nagios/rw/live" dhost=something.mozilla.com suser=someone suid=496 dproc=/usr/sbin/nagios msg=gid\\=496 euid\\=496 suid\\=496 fsuid\\=496 egid\\=496 sgid\\=496 fsgid\\=496 ses\\=20673 cwd\\="/" inode\\=00:00 dev\\=(null) mode\\=(null) ouid\\=(null) ogid\\=(null) rdev\\=(null) cn1Label=auid cn1=1579 cs1Label=Command cs1= cs2Label=Truncated cs2=No cs3Label=AuditKey cs3=(null) cs4Label=TTY cs4=(none) cs5Label=ParentProcess cs5=init cs6Label=MsgTruncated cs6=No
# anything starting with CEF:integer is a cef record
cefre = re.compile(r'''(CEF:[0-9]\|.*)''')
# declare list of cef fields we are interested in
validfields = [
    'act', 'app', 'cat', 'cnt', 'dvc', 'dvchost',
    'in', 'out', 'dst', 'dhost', 'dmac', 'dntdom',
    'dpt', 'dproc', 'duid', 'dpriv', 'duser', 'end',
    'fname', 'fsize', 'msg', 'rt', 'request', 'src',
    'shost', 'smac', 'sntdom', 'spt', 'spriv', 'suid',
    'suser', 'start', 'proto', 'cs1Label', 'cs2Label',
    'cs3Label', 'cs4Label', 'cs5Label', 'cs6Label',
    'cs1', 'cs2', 'cs3', 'cs4', 'cs5', 'cs6', 'cn1Label',
    'cn2Label', 'cn3Label', 'cn1', 'cn2', 'cn3', 'cn4',
    'request', 'requestClientApplication', 'requestMethod',
    'gid', 'euid', 'fsuid', 'egid', 'sgid', 'fsgid', 'ses', 'cwd',
    'inode', 'dev', 'mode', 'ouid', 'ogid', 'rdev'
]


def loggerTimeStamp(self, record, datefmt=None):
    return toUTC(datetime.now()).isoformat()


def initLogger():
    logger.level = logging.DEBUG
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    formatter.formatTime = loggerTimeStamp
    if options.output == 'syslog':
        logger.addHandler(SysLogHandler(address=(options.sysloghostname, options.syslogport), facility=logging.handlers.SysLogHandler.LOG_LOCAL4))
    else:
        sh = logging.StreamHandler(sys.stderr)
        sh.setFormatter(formatter)
        logger.addHandler(sh)


# buffer to hold fifo data until we get a complete log record since readlines/splitlines lies and returns text even without a newline.
class Buffer(deque):
    def put(self, iterable):
        for i in iterable:
            self.append(i)

    def peek(self, how_many):
        return ''.join([self[i] for i in xrange(how_many)])

    def get(self, how_many):
        return ''.join([self.popleft() for _ in xrange(how_many)])


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
    '''post logs to rabbitmq
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


def parseCEF(acef):
    '''parse a CEF record without regex to go as fast as possible
       returns a dict of CEF headers and a ['details'] subdict with the individual CEF items
    '''
    rawcefdict = {}
    cef = {}
    cef[u'version'] = 0
    cef[u'details'] = {}
    fields = []

    try:
        headers = acef.split('|')
        cef[u'details'][u'version'] = headers[0].replace('CEF:', '')
        cef[u'details'][u'devicevendor'] = headers[1]
        cef[u'details'][u'deviceproduct'] = headers[2]
        cef[u'details'][u'deviceversion'] = headers[3]
        cef[u'details'][u'signatureid'] = headers[4]
        cef[u'details'][u'name'] = headers[5]
        cef[u'details'][u'severity'] = headers[6]
        cef[u'summary'] = headers[5]
    except IndexError as e:
        logger.error('Index error parsing CEF headers in {0}'.format(acef[:200]))
        return None

    # get the non header fields including any pipes in target commands, etc. 
    # mlist = '|'.join(acef.split('|')[7:]).decode('ascii','ignore')
    # since fields are delimited by field=value<space>field=value
    # and we are reversing the text to find fields, 
    # add a beginning space else we miss the first field.
    # then grab everything after the cef header as ascii
    mlist = ' ' + '|'.join(acef.split('|')[7:]).decode('ascii','ignore')      
    # unescape any escaped field\\=value fields
    mlist = mlist.replace('\\=', '=')
    # no empty messages
    # mlist=mlist.replace('msg= ','')

    # before splitting on field=value, change valid fields to a token splitter
    for f in validfields:
        if ' {0}='.format(f) in mlist:
            mlist = mlist.replace('{0}='.format(f), '{0}:=:'.format(f))
    mlist = mlist.split(':=:')

    i = 0
    try:
        for i, x in enumerate(reversed(mlist)):
            i = i + 1
            slast = mlist[-(i+1)]
            cut = slast.split()
            cut2 = cut[-1]
            fields.insert(i, cut2)
            rawcefdict.update({cut2.lower():x})
            mlist[-(i+1)] = " ".join(cut[0:-1])
    except IndexError as e:
        pass

    # fix up custom field names
    # cs6Label MsgTruncated cs6 No
    for field in fields:
        if 'label' in field.lower():
            # this is a label for another field..fix up our dict to have the label as key and data as value
            if field.lower().replace('label', '') in rawcefdict.keys():
                cef['details'][rawcefdict[field.lower()].lower()] = rawcefdict[field.lower().replace('label', '')].decode('ascii', 'ignore')
                rawcefdict.pop(field.lower().replace('label', ''))
            rawcefdict.pop(field.lower(), '')

    # add whatever is left (non label field or value) to the cef dictionary
    for k, v in rawcefdict.iteritems():
        cef['details'][k.decode('ascii', 'ignore').lower()] = v.decode('ascii', 'ignore')

    # pick an eventtimestamp if one exists.
    if 'start' in cef['details'].keys():
        cef['timestamp'] = toUTC(cef['details']['start']).isoformat()
    elif 'end' in cef['details'].keys():
        cef['timestamp'] = toUTC(cef['details']['end']).isoformat()
    elif 'rt' in cef['details'].keys():
        cef['timestamp'] = toUTC(cef['details']['rt']).isoformat()
    else:
        cef['timestamp'] = toUTC(datetime.now()).isoformat()
    return cef


def nonBlockRead(fd):
    try:
        fl = fcntl.fcntl(fd, fcntl.F_GETFL)
        fcntl.fcntl(fd, fcntl.F_SETFL, fl | os.O_NONBLOCK)
        out = os.read(fd, 1024)
        if out is None:
            return ''
        else:
            return out
    except OSError as e:
        logger.error('%r' % e)
        return ''
    except Exception as e:
        logger.error('%r' % e)


def main():
    # create a list of logs we can append json to and call for a post when we want.
    logcache = Queue()

    logger.info('started')
    if exists(options.logfile):
        # start a process to post our stuff.
        logcache = JoinableQueue()
        postingProcess = Process(target=postLogs, args=(logcache,), name="cef2mozdefMQPost")
        postingProcess.start()
        # open the fifo in non blocking read only mode.
        fd = os.open(options.logfile, os.O_NONBLOCK | os.O_RDONLY)
        p = select.epoll()
        p.register(fd, select.EPOLLIN)
        buf = None
        bufa = Buffer()
        bufb = Buffer()
        cefDict = None
        while True:
            try:
                # poll the fifo to see if it has data
                events = p.poll()
                buf = None
                for ffd, ev in events:
                    if ev & select.EPOLLIN:
                        try:
                            buf = os.read(fd, options.fiforeadsize)
                        except OSError as e:
                            if e.errno == errno.EAGAIN or e.errno == errno.EWOULDBLOCK:
                                # try again, or would block
                                pass
                            else: raise
                        if buf is not None:
                            # we got some data, maybe enough for a log record + \n
                            bufa.append(buf)
                    else:
                        # non read event occurred, wait a bit and poll again.
                        time.sleep(.01)

                if '\n' in ''.join(bufa):
                    # new line/end of log is found
                    for line in ''.join(bufa).splitlines(True):
                        if '\n' in line:
                            # logger.debug(line.strip())
                            for acef in cefre.findall(line):
                                cefDict = parseCEF(acef)
                                # logger.debug(json.dumps(cefDict))
                                # append json to the list for posting
                                if cefDict is not None:
                                    # logger.debug(json.dumps(cefDict))
                                    logcache.put(json.dumps(cefDict))
                        else:
                            bufb.append(line)
                    bufa.clear()
                    bufa.append(''.join(bufb))
                    bufb.clear()
            except KeyboardInterrupt:
                sys.exit(1)
            except ValueError as e:
                logger.fatal('Exception while handling CEF message: %r' % e)
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
    # how much to read in a chunk from the fifo
    options.fiforeadsize = getConfig('fiforeadsize', 2048, options.configfile)

if __name__ == '__main__':
    parser = OptionParser()
    parser.add_option("-c", dest='configfile', default=sys.argv[0].replace('.py', '.conf'), help="configuration file to use")
    (options, args) = parser.parse_args()
    initConfig()
    initLogger()
    main()
