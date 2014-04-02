#!/usr/bin/env python
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
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
from multiprocessing import Process, Queue
import random
import errno
import select
import glob2
from os import stat

#setting this globally to allow requests to establish a keep alive session with async workers.
httpsession = FuturesSession(max_workers=10)
httpsession.trust_env=False #turns off needless and repetitive .netrc check for creds

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
            objDate=parse(time.ctime(float(suspectedDate)),fuzzy=True)
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
            self._fh = open(filename, "r")
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
    posts=[]
    
    while not logcache.empty():
        postdata=logcache.get()
        if len(postdata)>0:
            url=random.choice(options.urls)
            r=httpsession.post(url,data=postdata,stream=False)
            posts.append((r,postdata,url))
        for p,postdata,url in posts:
            try:
                if p.result().status_code >=500:
                    logger.error("exception posting to %s %r [will retry]\n"%(url,p.result().status_code))
                    #try again later when the next message in forces other attempts at posting.
                    logcache.put(postdata)
            except Exception as e:
                    logger.fatal("exception posting to %s %r %r [will not retry]\n"%(url,e,postdata))
                


def parseCEF(acef):
    fields=[]
    rawfielddict={}
    finalfielddict={}
    cef=dict(version=0,fields={})
    
    #some CEF records escape the equals with \= to cram extra fields in the 'msg' field. Undo that and get them as event.details
    if re.search('msg=(\w+\\\\=)',acef):
        acef=acef.replace('msg=','')
        if '\\=' in acef:
            acef=acef.replace('\\=','=')
        
    #logger.debug(line)    
    
    #get a list of the field names we will be handling
    fields=ceffieldre.findall(acef)
    
    #for each field name, get the value of field=value including spaces
    #by grabbing everything up to the next field=value
    #logger.debug(fields)
    for field in fields:
        if fields.index(field)==len(fields)-1: #end of list
            fieldvaluere=re.compile('{0}=(.*)'.format(field))
        else:
            nextfield=fields[(fields.index(field)+1)]
            fieldvaluere=re.compile('{0}=(.*?) {1}='.format(field,nextfield))
        fieldvalue=fieldvaluere.findall(acef)
        if len(fieldvalue)>0:
            #logger.debug('CEF {0} {1}'.format(field,fieldvalue[0]))
            rawfielddict[field.lower()]=fieldvalue[0]   

    #CEF includes the capability to label fields
    #cs6Label MsgTruncated cs6 No
    #figure these out and rename them accordingly.
    #logger.debug(acef)
    try:
        for field in fields:
            if 'label' in field.lower():
                #this is a label for another field..fix up our dict to have the label as key and data as value
                if field.lower().replace('label','') in rawfielddict.keys():
                    finalfielddict[rawfielddict[field.lower()]]=rawfielddict[field.lower().replace('label','')].decode('ascii','ignore')
                    rawfielddict.pop(field.lower().replace('label',''))
                rawfielddict.pop(field.lower(),'')
    except KeyError as e:
        logger.error('Key error while renaming cef labels: {0} {1}'.format(acef,e))
    
    try:         
        #add whatever is left in the raw field dict to the final dict
        for k,v in rawfielddict.iteritems():
            finalfielddict[k]=v.decode('ascii','ignore')
        cef['fields']=finalfielddict
        #pick an eventtimestamp if one exists. 
        if 'start' in rawfielddict.keys():
            cef['timestamp']=toUTC(rawfielddict['start']).isoformat()
        elif 'end' in rawfielddict.keys():
            cef['timestamp']=toUTC(rawfielddict['end']).isoformat()
        elif 'rt' in rawfielddict.keys():
            cef['timestamp']=toUTC(rawfielddict['rt']).isoformat()
        else:
            cef['timestamp']=toUTC(datetime.now()).isoformat()
        
        #grab all the CEF headers and add them as fields
        headers=cefheaderre.findall(acef)
        cef['fields']['version']=headers[0].replace('CEF:','')
        cef['fields']['devicevendor']=headers[1]
        cef['fields']['deviceproduct']=headers[2]
        cef['fields']['deviceversion']=headers[3]
        cef['fields']['signatureid']=headers[4]
        cef['fields']['name']=headers[5]
        cef['fields']['severity']=headers[6]
        
        cef['summary']=headers[5]
        return cef
    except (IndexError,ValueError) as e:
        logger.error('Exception while creating final dict: {0} {1}'.format(acef,e))
    
                
def main():
    #create a list of logs we can append json to and call for a post when we want.
    logcache=Queue()
    
    logger.info('started')
    notDone=True
    while notDone: 
        for afile in glob2.iglob(options.filemask):
            if exists(afile): #sometimes files can move/archive while we iterate the list
                try: 
                    #have pygtail feed us lines 
                    pt = Pygtail(afile,pretend=False)
                    for line in pt:                
                        for acef in cefre.findall(line):
                            cefDict=parseCEF(acef)
                            #logger.debug(json.dumps(cefDict))
                        
                            #append json to the list for posting
                            if cefDict is not None:
                                logcache.put(json.dumps(cefDict))        
                        if not logcache.empty():
                            #postLogs(logcache)
                            postingProcess=Process(target=postLogs,args=(logcache,),name="cef2mozdefHTTPPost")
                            postingProcess.start()
                        pt._update_offset_file()
                except KeyboardInterrupt:
                    sys.exit(1)
                except ValueError as e:
                    logger.fatal('Exception while handling CEF message: %r'%e)
                    sys.exit(1)
        notDone=False
        time.sleep(.001)
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
    main()
