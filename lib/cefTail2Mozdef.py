#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
# Copyright (c) 2014 Mozilla Corporation
#
# Contributors:
# Jeff Bryner jbryner@mozilla.com

import os
import sys
from configlib import getConfig,OptionParser
import logging
from logging.handlers import SysLogHandler
from datetime import datetime
from datetime import timedelta
from dateutil.parser import parse
import pytz
import re
import json
from os.path import exists, getsize
import time
from requests_futures.sessions import FuturesSession
from collections import deque
import fcntl
from multiprocessing import Process, Queue, JoinableQueue
from Queue import Empty, Full
import random
import errno
import select
import glob2
import glob
from os import stat
from collections import deque

class Buffer(deque):
    def put(self, iterable):
        for i in iterable:
            self.append(i)

    def peek(self, how_many):
        return ''.join([self[i] for i in xrange(how_many)])

    def get(self, how_many):
        return ''.join([self.popleft() for _ in xrange(how_many)])
    
    
logger = logging.getLogger(sys.argv[0])

def loggerTimeStamp(self, record, datefmt=None):
    return toUTC(datetime.now()).isoformat()

def initLogger():
    logger.level = logging.DEBUG
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    formatter.formatTime = loggerTimeStamp
    if options.output == 'syslog':
        logger.addHandler(SysLogHandler(address=(options.sysloghostname, options.syslogport)))
    else:
        sh = logging.StreamHandler(sys.stderr)
        sh.setFormatter(formatter)
        logger.addHandler(sh)

#sample CEF record:
#CEF:0|Unix|auditd|1|CHMOD|CHMOD failed|3|end=1391190619 fname="/var/log/nagios/rw/live" dhost=something.mozilla.com suser=someone suid=496 dproc=/usr/sbin/nagios msg=gid\\=496 euid\\=496 suid\\=496 fsuid\\=496 egid\\=496 sgid\\=496 fsgid\\=496 ses\\=20673 cwd\\="/" inode\\=00:00 dev\\=(null) mode\\=(null) ouid\\=(null) ogid\\=(null) rdev\\=(null) cn1Label=auid cn1=1579 cs1Label=Command cs1= cs2Label=Truncated cs2=No cs3Label=AuditKey cs3=(null) cs4Label=TTY cs4=(none) cs5Label=ParentProcess cs5=init cs6Label=MsgTruncated cs6=No
cefre=re.compile(r'''(CEF:[0-9]\|.*)''')                        #anything starting with CEF:integer
cefitemre=re.compile(r'''([a-z,A-Z,0-9]{1,10}=.+?) ''')         #anything like field=value (bug if value contains a space)
cefheaderre=re.compile(r'''(.+?)\|''')                          #anything between | is a header value

ceffieldre=re.compile(r'''(\w+)=''')                           #cef field keys (something=value)
#cefitemre=re.compile(r'''([a-z,A-Z,0-9]{1,10}=.+?)(\w+=)''')         #anything like field=value

def isNumber(s):
    'check if a token is numeric, return bool'
    try:
        float(s) # for int, long and float
    except ValueError:
        try:
            complex(s) # for complex
        except ValueError:
            return False
    return True

def toUTC(suspectedDate,localTimeZone=None):
    '''make a UTC date out of almost anything'''
    utc=pytz.UTC
    objDate=None
    if localTimeZone is None:
        localTimeZone=options.defaultTimeZone    
    try:
        if type(suspectedDate)==datetime:
            objDate=suspectedDate
        elif isNumber(suspectedDate):   #epoch?
            #objDate=parse(time.ctime(float(suspectedDate)),fuzzy=False)
            objDate=datetime.fromtimestamp(float(suspectedDate))
        elif type(suspectedDate)==str:
            objDate=parse(suspectedDate,fuzzy=True)
        
        if objDate.tzinfo is None:
            objDate=pytz.timezone(localTimeZone).localize(objDate)
            objDate=utc.normalize(objDate)
        else:
            objDate=utc.normalize(objDate)
        if objDate is not None:
            objDate=utc.normalize(objDate)
    except ValueError:
        pass
        
    return objDate

class Pygtail(object):
    """
    Creates an iterable object that returns only unread lines.
    """
    def __init__(self, filename, offset_file=None, paranoid=False,pretend=False):
        self.filename = filename
        self.paranoid = paranoid
        self._offset_file = offset_file or "%s.offset" % self.filename
        self._offset_file_inode = 0
        self._offset = 0
        self._fh = None
        self._rotated_logfile = None
        self.pretend=pretend

        # if offset file exists and non-empty, open and parse it
        if exists(self._offset_file) and getsize(self._offset_file):
            offset_fh = open(self._offset_file, "r")
            (self._offset_file_inode, self._offset) = \
                [int(line.strip()) for line in offset_fh]
            offset_fh.close()
            if self._offset_file_inode != stat(self.filename).st_ino:
                # The inode has changed, so the file might have been rotated.
                # Look for the rotated file and process that if we find it.
                self._rotated_logfile = self._determine_rotated_logfile()

    def __del__(self):
        if self._filehandle():
            self._filehandle().close()

    def __iter__(self):
        return self

    def next(self):
        """
        Return the next line in the file, updating the offset.
        """
        try:
            line = next(self._filehandle())
        except StopIteration:
            # we've reached the end of the file; if we're processing the
            # rotated log file, we can continue with the actual file; otherwise
            # update the offset file
            if self._rotated_logfile:
                self._rotated_logfile = None
                self._fh.close()
                self._offset = 0
                self._update_offset_file()
                # open up current logfile and continue
                try:
                    line = next(self._filehandle())
                except StopIteration:  # oops, empty file
                    self._update_offset_file()
                    raise
            else:
                self._update_offset_file()
                raise

        if self.paranoid:
            self._update_offset_file()

        return line

    def __next__(self):
        """`__next__` is the Python 3 version of `next`"""
        return self.next()

    def readlines(self):
        """
        Read in all unread lines and return them as a list.
        """
        return [line for line in self]

    def read(self):
        """
        Read in all unread lines and return them as a single string.
        """
        lines = self.readlines()
        if lines:
            return ''.join(lines)
        else:
            return None

    def _filehandle(self):
        """
        Return a filehandle to the file being tailed, with the position set
        to the current offset.
        """
        if not self._fh or self._fh.closed:
            filename = self._rotated_logfile or self.filename
            #self._fh = open(filename, "r")
            self._fh = os.open(filename,os.O_RDONLY)
            self._fh.seek(self._offset)

        return self._fh

    def _update_offset_file(self):
        """
        Update the offset file with the current inode and offset.
        """
        if not self.pretend:
            offset = self._filehandle().tell()
            inode = stat(self.filename).st_ino
            fh = open(self._offset_file, "w")
            fh.write("%s\n%s\n" % (inode, offset))
            fh.close()

    def _determine_rotated_logfile(self):
        """
        We suspect the logfile has been rotated, so try to guess what the
        rotated filename is, and return it.
        """
        for rotated_filename in self._check_rotated_filename_candidates():
            if exists(rotated_filename) and stat(rotated_filename).st_ino == self._offset_file_inode:
                return rotated_filename
        return None

    def _check_rotated_filename_candidates(self):
        """
        Check for various rotated logfile filename patterns and return the 
        matches we find.
        """
        candidates=[]
        # savelog(8)
        candidate = "%s.0" % self.filename
        if (exists(candidate) and exists("%s.1.gz" % self.filename) and
            (stat(candidate).st_mtime > stat("%s.1.gz" % self.filename).st_mtime)):
            candidates.append(candidate)

        # logrotate(8)
        candidate = "%s.1" % self.filename
        if exists(candidate):
            candidates.append(candidate)

        # dateext rotation scheme
        for candidate in glob.glob("%s-[0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9]" % self.filename):
            candidates.append(candidate)

        # for TimedRotatingFileHandler
        for candidate in glob.glob("%s.[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]" % self.filename):
            candidates.append(candidate)

        return candidates

def postLogs(logcache):
    #post logs asynchronously with requests workers and check on the results
    #expects a queue object from the multiprocessing library
    #setting this within the processs to allow requests to establish a keep alive session with async workers.
    httpsession = FuturesSession(max_workers=2)
    httpsession.trust_env=False #turns off needless and repetitive .netrc check for creds
    canQuit=False
    logger.info('started posting process')
    def backgroundcallback(session, response):
        #release the connection back to the pool
        try: 
            r=response.result()
            response.close()
        except Exception as e:
            logger.error('Exception while posting message: %r'%e)

    while True:
        try:
            #see if we have anything to post
            #waiting a bit to not end until we are told we can stop.
            postdata=logcache.get(False,30)
            if postdata is None:
                #signalled from parent process that it's ok to stop.
                logcache.task_done()
                canQuit=True
                
            elif len(postdata)>0:
                url=random.choice(options.urls)
                r=httpsession.post(url,data=postdata,stream=False)
                logcache.task_done()
        except Empty as e:
            if canQuit:
                logger.info('signaling shutdown for threadpool executor')
                httpsession.executor.shutdown(wait=True)
                break

    logger.info('{0} done'.format('log posting task'))

def parseCEF(acef):
    '''parse a CEF record without regex to go as fast as possible
       returns a dict of CEF headers and a ['details'] subdict with the individual CEF items
    '''
    rawcefdict = {}
    cef={}
    cef['version']=0
    cef['details']={}
    fields=[]
    
    headers=acef.split('|')
    cef['details']['version']=headers[0].replace('CEF:','')
    cef['details']['devicevendor']=headers[1]
    cef['details']['deviceproduct']=headers[2]
    cef['details']['deviceversion']=headers[3]
    cef['details']['signatureid']=headers[4]
    cef['details']['name']=headers[5]
    cef['details']['severity']=headers[6]
    cef['summary']=headers[5]
    
    #get the non header fields including any pipes in target commands, etc. 
    mlist = '|'.join(acef.split('|')[7:]).decode('ascii','ignore')
    #unescape any escaped field\\=value fields
    mlist=mlist.replace('\\=', '=')
    #no empty messages 
    mlist=mlist.replace('msg= ','').split('=')
    
    i=0
    try:
        for i,x in enumerate(reversed(mlist)):
            i = i + 1
            slast = mlist[-(i+1)]
            cut = slast.split()
            cut2 = cut[-1]
            fields.insert(i,cut2)
            rawcefdict.update({cut2.lower():x})
            mlist[-(i+1)] = " ".join(cut[0:-1])
    except IndexError as e:
        pass
    #fix up custom field names
    #cs6Label MsgTruncated cs6 No
    for field in fields:
        if 'label' in field.lower():
            #this is a label for another field..fix up our dict to have the label as key and data as value
            if field.lower().replace('label','') in rawcefdict.keys():
                cef['details'][rawcefdict[field.lower()]]=rawcefdict[field.lower().replace('label','')].decode('ascii','ignore')    
                rawcefdict.pop(field.lower().replace('label',''))
            rawcefdict.pop(field.lower(),'')
    #add whatever is left (non label field or value) to the cef dictionary
    for k,v in rawcefdict.iteritems():
        cef['details'][k]=v.decode('ascii','ignore')
    #pick an eventtimestamp if one exists. 
    if 'start' in cef['details'].keys():
        cef['timestamp']=toUTC(cef['details']['start']).isoformat()
    elif 'end' in cef['details'].keys():
        cef['timestamp']=toUTC(cef['details']['end']).isoformat()
    elif 'rt' in cef['details'].keys():
        cef['timestamp']=toUTC(cef['details']['rt']).isoformat()
    else:
        cef['timestamp']=toUTC(datetime.now()).isoformat()        
    return cef

def nonBlockRead(fd):
    try:
        fl = fcntl.fcntl(fd, fcntl.F_GETFL)
        fcntl.fcntl(fd, fcntl.F_SETFL, fl | os.O_NONBLOCK)
        out= os.read(fd,1024)
        if out !=None:
            return out
        else:
            return ''
    except Exception as e:
        logger.error('%r'%e)

def readCEFFile(afile):
    if exists(afile): #sometimes files can move/archive while we iterate the list
        try:
            #start a process to post our stuff.
            logcache=JoinableQueue()
            postingProcess=Process(target=postLogs,args=(logcache,),name="cef2mozdefHTTPPost")
            postingProcess.start()
            #tail a file to feed us lines
            #yielding a line on newline, buffering input in between
            fh = os.open(afile, os.O_RDONLY | os.O_NONBLOCK)
            os.lseek(fh, 0, os.SEEK_END)
            bufa=Buffer()
            bufb=Buffer()
            while True:
                time.sleep(0.001) # Wait a little
                bufa.append(nonBlockRead(fh))
                if '\n' in ''.join(bufa):  #new line/end of log is found
                    for line in ''.join(bufa).splitlines(True):
                        if '\n' in line:
                            cefDict=parseCEF(line.strip())
                            #logger.debug(json.dumps(cefDict))
                            #append json to the list for posting
                            if cefDict is not None:
                                logcache.put(json.dumps(cefDict)) 
                        else:
                            bufb.append(line)
                    bufa.clear()
                    bufa.append(''.join(bufb))
                    bufb.clear()
            logger.info('{0} done'.format(afile))
            logger.info('waiting for posting to finish')
            logcache.put(None)
            logcache.close()
            #logger.info('posting done')
        except KeyboardInterrupt:
            sys.exit(1)
        except ValueError as e:
            logger.fatal('Exception while handling CEF message: %r'%e)
            sys.exit(1)    
def main():
    logger.info('started')
    notDone=True
    while notDone:
        #anyone done?
        for process,file in readers:
            if not process.is_alive():
                logger.info('{0}/{1} marked as done'.format(process,file))
                readers.remove((process,file))
        
        for afile in glob2.iglob(options.filemask):
            #logger.debug('noticed file {0}'.format(afile))
            #if we aren't reading a file
            #spin up a process to read the file
            activefiles=[]
            for process,filename in readers:
                activefiles.append(filename)
            if afile not in activefiles:            
                logger.info('starting a reader for {0}'.format(afile))
                readingProcess=Process(target=readCEFFile,args=(afile,),name="cef2mozdefReadFile")
                readers.append((readingProcess,afile))
                readingProcess.start()
                
        #if we are reading a file no longer in the list of active files (rotated, etc),
        #tell it's reader it's ok to stop.
        for process,filename in readers:
            if filename not in glob2.iglob(options.filemask):
                logger.info('{0} no longer valid, stopping file reader'.format(filename))
                process.terminate()
                process.join()
            
        #change this if you want it to stop (cronjob, or debugging), else it will run forever (ala /etc/init service)
        #notDone=False
        time.sleep(2)
    logger.info('finished')

def initConfig():
    options.output=getConfig('output','stdout',options.configfile)                      #output our log to stdout or syslog
    options.sysloghostname=getConfig('sysloghostname','localhost',options.configfile)   #syslog hostname
    options.syslogport=getConfig('syslogport',514,options.configfile)                   #syslog port
    options.filemask=getConfig('filemask','*.log',options.configfile)
    options.urls=list(getConfig('urls','http://localhost:8080/cef/',options.configfile).split(','))
     #change this to your default zone for when it's not specified
    options.defaultTimeZone=getConfig('defaulttimezone','US/Pacific',options.configfile)
    
if __name__ == '__main__':
    parser=OptionParser()
    parser.add_option("-c", dest='configfile' , default=sys.argv[0].replace('.py','.conf'), help="configuration file to use")
    (options,args) = parser.parse_args()
    initConfig()
    initLogger()

    readers=[]
    main()