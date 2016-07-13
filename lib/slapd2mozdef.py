#!/usr/bin/env python
import os
import sys
from configlib import getConfig,OptionParser
import re
import glob2
import glob
from os.path import exists, getsize
from os import stat
from time import sleep
import requests
import dateutil.parser
import datetime
from dateutil.tz import tzlocal
import json
from requests_futures.sessions import FuturesSession

'''
Search for slapd transactions and parse out the interesting bits:

Jan  2 08:01:57 ldap1 slapd[24398]: conn=15824148 fd=28 ACCEPT from IP=10.22.70.209:18451 (IP=0.0.0.0:389)
Jan  2 08:01:57 ldap1 slapd[24398]: conn=15824148 op=0 BIND dn="mail=someone@somewhere.com,o=com,dc=somewhere" method=128
Jan  2 08:01:57 ldap1 slapd[24398]: slap_queue_csn: queing 0x7fab377fc900 20140102160157.075233Z#000000#000#000000
Jan  2 08:01:57 ldap1 slapd[24398]: slap_graduate_commit_csn: removing 0x7faaf3a34e80 20140102160157.075233Z#000000#000#000000
Jan  2 08:01:57 ldap1 slapd[24398]: conn=15824148 op=0 RESULT tag=97 err=49 text=
Jan  2 08:01:57 ldap1 slapd[24398]: conn=15824148 fd=28 closed (connection lost)

syslog/udp so lines don't come in order, don't expect them to. 

'''

errCodes={}
errCodes[None] = "UNKNOWN"
errCodes[0] = "LDAP_SUCCESS"
errCodes[32] = "LDAP_NO_SUCH_OBJECT"
errCodes[49] = "LDAP_INVALID_CREDENTIALS"
errCodes[50] = "LDAP_INSUFFICIENT_ACCESS"
errCodes[53] = "LDAP_UNWILLING_TO_PERFORM"
errCodes[65] = "LDAP_OBJECT_CLASS_VIOLATION"
errCodes[80] = "LDAP_OTHER"

bindConnre= re.compile(r'''conn=(?P<conn>\d+) op=(?P<op>\d+) BIND\s+dn="mail=(?P<dn>.*?)" ''')
httpsession = FuturesSession(max_workers=20)
httpsession.trust_env=False #turns of needless .netrc check for creds

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


def searchforBind(line,bindDetails):
    '''catch every bind of interest in a line, store in a dictionary to allow backtrack into the srcIP and bind result.'''
    for bindConn in bindConnre.findall(line):
        if '{0}:{1}:{2}'.format(bindConn[0],bindConn[1],bindConn[2]) not in bindDetails.keys():
            #a new bind transaction we've not seen with default values
            bindDetails['{0}:{1}:{2}'.format(bindConn[0],bindConn[1],bindConn[2])]=dict(conn=bindConn[0],op=bindConn[1],dn=bindConn[2],errCode=None,result='unknown',ipAddress='0.0.0.0',eventtime=dateutil.parser.parse(line[:20],fuzzy=True,tzinfos=tzlocal).isoformat())

def searchforBindResult(line,bindDetails,linecache):
    '''match outstanding binds without results to any new RESULT lines'''
    cache=''.join(linecache)
    for bind in bindDetails:
        if bindDetails[bind]['errCode'] is None:       
            #print('searching...{0} {1}'.format(bindDetails[bind]['conn'],bindDetails[bind]['op']))
            errCodere=re.compile(r'''conn={0} op={1} RESULT tag=\d+ err=(\d+) '''.format(bindDetails[bind]['conn'],bindDetails[bind]['op']))
    
            for errCode in errCodere.findall(cache):
                bindDetails[bind]['result']=errCodes[int(errCode)]
                bindDetails[bind]['errCode']=int(errCode)
        if bindDetails[bind]['ipAddress']=='0.0.0.0':       
            srcIPre=re.compile(r'''conn={0}.*?ACCEPT from IP=(.*?):\d+ '''.format(bindDetails[bind]['conn']))
            for srcIP in srcIPre.findall(cache):
                bindDetails[bind]['ipAddress']=srcIP    

def postBindResults(bindDetails,pt,linecache,eof=False):
    '''post our results via http using a keepalive session'''
    #httpsession = requests.Session() is declared globally to avoid performance hit of instantiating it per line.
    posts=[]
    cache=''.join(linecache)
    for bind in bindDetails.keys():
        #if we have a complete record, or we have no hope of getting a complete record, or we are at the end of file: post the transaction.
        if (bindDetails[bind]['errCode'] is not None and bindDetails[bind]['ipAddress'] !='0.0.0.0') \
            or (bindDetails[bind]['conn'] not in cache) \
            or (eof):
            try:            
                log=('{0} {1} srcIP={2}'.format(bindDetails[bind]['result'],bindDetails[bind]['dn'],bindDetails[bind]['ipAddress']))
                #format a dictionary object to post in json
                eventlog=dict(message=log,timestamp=bindDetails[bind]['eventtime'])
                eventlog['details.dn']=bindDetails[bind]['dn']
                eventlog['details.result']=bindDetails[bind]['result']
                eventlog['details.sourceipaddress']=bindDetails[bind]['ipAddress']
                if 'success' in bindDetails[bind]['result'].lower():
                    eventlog['details.success']=True
                else:
                    eventlog['details.success']=False
                eventlog['tags']=['ldap']
                #add all source lines to the message for forensics/chain of custody
                eventlog['details.source']=''
                for line in linecache:
                    if bindDetails[bind]['conn'] in line:
                        eventlog['details.source']+=line            
             
                r=httpsession.post(options.url,json.dumps(eventlog))
                posts.append(r)
                #print("%r"%r)
                #sys.stdout.write('{0}\n'.format(json.dumps(eventlog)))
            except Exception as e:
                sys.stderr.write("slapd2mozdef.py exception posting to %s %r"%(options.url,e))
                sys.exit(1)
    for p in posts:
        try: 
            if p.result().status_code!=200:
                sys.stderr.write("slapd2mozdef.py exception posting to %s %r"%(options.url,p.result().status_code))
                sys.exit(1)
        except Exception as e:
                sys.stderr.write("slapd2mozdef.py exception posting to %s %r"%(options.url,e))
                sys.exit(1)            
    #update our position in the file
    pt.pretend=False
    pt._update_offset_file()
    pt.pretend=True

def trimBindDetails(bindDetails,linecache):
    '''cull the dictionary of transactions where we've found the entire record'''
    cache=''.join(linecache)
    for bind in bindDetails.keys():
        if bindDetails[bind]['errCode'] is not None and bindDetails[bind]['ipAddress'] !='0.0.0.0':
            bindDetails.pop(bind,None)
        elif bindDetails[bind]['conn'] not in cache:
            '''we don't stand a chance of finding the missing bits'''
            bindDetails.pop(bind,None)

def main():
    '''For each file matching our filemask
       read in lines until we've got a complete slapd connection/termination
       parse out the interesting transactions and move on to the next
       sleeping in between to be nice to our cpu for really large files
    '''
    
    for afile in glob2.iglob(options.filemask):
        #cache list of log lines to help deal with the multi-line slapd format
        linecache=[]
        
        #defaults
        ipAddress='0.0.0.0'
        bindName='Unknown'
        errCode=None
        errName='Unknown'
        
        #dictionary to store bits of bind transactions as we find them in the multi-line logs
        bindDetails={}
        
        if exists(afile): #sometimes files can move/archive while we iterate the list
            #have pygtail feed us lines without incrementing the offset until we've posted any results we've found.
            pt = Pygtail(afile,pretend=True)
            for line in pt:
                if 'slapd' in line and ('ACCEPT' in line or 'RESULT' in line or 'BIND' in line ):
                    #store lines until we match a multi line slapd connection structure
                    #ACCEPT yields the source IP, BIND yields the dn someone@somewhere.com, RESULT yields the success/failure
                    if len(linecache)>options.cachelength:
                        linecache.remove(linecache[0])
                    linecache.append(line)
                    
                    searchforBind(line,bindDetails)
    
                    if 'RESULT' in line:
                        #maybe it's the termination of an earlier bind attempt
                        searchforBindResult(line,bindDetails,linecache)
                        postBindResults(bindDetails,pt,linecache)
                        trimBindDetails(bindDetails,linecache)
                    sleep(.00001)  #be nice, but not too nice
        #post any remaining bindDetails
        postBindResults(bindDetails,pt,linecache,True)

def initConfig():
    #change this to your default zone for when it's not specified
    options.defaultTimeZone=getConfig('defaulttimezone','US/Pacific',options.configfile)    
    options.filemask=getConfig('filemask','*.log',options.configfile)
    options.cachelength=getConfig('cachelength',100,options.configfile)
    options.url=getConfig('url','http://localhost:9200',options.configfile)
    options.bindignore=getConfig('bindignore','',options.configfile)  #space delimited list of words/usernames/items if found in BIND dn="something" to ignore
 
if __name__ == '__main__':
    parser=OptionParser()
    parser.add_option("-c", dest='configfile' , default='', help="configuration file to use")
    (options,args) = parser.parse_args()
    initConfig()
    main()
