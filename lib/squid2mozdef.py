#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
# Copyright (c) 2014 Mozilla Corporation

# Contributor: gdestuynder@mozilla.com
# Contributor: jbryner@mozilla.com
# Contributor: jclaudius@mozilla.com

import copy
import os
import sys
import re
import json
import glob
import string
import ConfigParser
import tempfile
import logging
import socket
from logging.handlers import SysLogHandler
from requests import Session
from optparse import OptionParser
from datetime import datetime
from dateutil.tz import tzlocal
from os import stat
from os.path import exists, getsize

"""
    Script to monitor changes in a squid log  file and post as json to mozdef
    Uses the pygtail class to tail lines and follow rotated files
"""


class MozDefError(Exception):
    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return repr(self.msg)


class MozDefEvent():
    # create requests session to allow for keep alives
    httpsession = Session()
    # Turns off needless and repetitive .netrc check for creds
    httpsession.trust_env = False
    debug = False
    verify_certificate = '/etc/ssl/certs/ca-bundle.crt'
    # Never fail (ie no unexcepted exceptions sent to user, such as server/network not responding)
    fire_and_forget_mode = True
    log = {}
    log['timestamp'] = datetime.isoformat(datetime.now(tzlocal()))
    log['hostname'] = socket.getfqdn()
    log['processid'] = os.getpid()
    log['processname'] = sys.argv[0]
    log['severity'] = 'INFO'
    log['summary'] = None
    log['category'] = 'event'
    log['tags'] = list()
    log['details'] = dict()

    def __init__(self, url='http://localhost/events', summary=None, category='event', severity='INFO', tags=[], details={}):
        self.summary = summary
        self.category = category
        self.severity = severity
        self.tags = tags
        self.details = details
        self.url = url
        self.hostname = socket.getfqdn()

    def send(self, timestamp=None, summary=None, category=None, severity=None, tags=None, details=None, hostname=None):
        log_msg = copy.copy(self.log)

        if timestamp is None:
            log_msg['timestamp'] = self.timestamp
        else:
            log_msg['timestamp'] = timestamp
            
        if summary is None:
            log_msg['summary'] = self.summary
        else:
            log_msg['summary'] = summary

        if category is None:
            log_msg['category'] = self.category
        else:
            log_msg['category'] = category

        if severity is None:
            log_msg['severity'] = self.severity
        else:
            log_msg['severity'] = severity

        if tags is None:
            log_msg['tags'] = self.tags
        else:
            log_msg['tags'] = tags

        if details is None:
            log_msg['details'] = self.details
        else:
            log_msg['details'] = details

        if hostname is None:
            log_msg['hostname'] = self.hostname
        else:
            log_msg['hostname'] = hostname            

        if type(log_msg['details']) != dict:
            raise MozDefError('details must be a dict')
        elif type(log_msg['tags']) != list:
            raise MozDefError('tags must be a list')
        elif summary is None:
            raise MozDefError('Summary is a required field')

        if self.debug:
            print(json.dumps(log_msg, sort_keys=True, indent=4))
            #return

        try:
            r = self.httpsession.post(self.url, json.dumps(log_msg), verify=self.verify_certificate)
        except Exception as e:
            if not self.fire_and_forget_mode:
                raise e

def createLogRecord(lineIn):
    # make an event message
    lineIn = lineIn.strip()
    fields = lineIn.split()
    
    timestamp = datetime.fromtimestamp(float(fields[0])).isoformat()
    sourceipaddress = fields[2]
    proxyaction = fields[3]
    tcpaction = fields[5]
    destination = fields[6]
    mimetype = fields[9]
    
    log = {}
    log['category'] = 'squid'
    log['summary'] = 'squid: {0} {1}'.format(proxyaction, destination)
    log['severity'] = 'INFO'
    log['details'] = dict()
    log['details']['sourceipaddress'] = sourceipaddress
    log['details']['proxyaction'] = proxyaction
    log['details']['tcpaction'] = tcpaction
    log['details']['destination'] = destination
    log['details']['mimetype'] = mimetype
    log['timestamp'] = datetime.isoformat(datetime.now(tzlocal()))
    return(log)


class Pygtail(object):
    """
    Creates an iterable object that returns only unread lines.
    """
    def __init__(self, filename, offset_file=None, paranoid=False, pretend=False):
        self.filename = filename
        self.paranoid = paranoid
        self._offset_file = offset_file or "%s.offset" % self.filename
        self._offset_file_inode = 0
        self._offset = 0
        self._fh = None
        self._rotated_logfile = None
        self.pretend = pretend

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
        candidates = []
        # savelog(8)
        candidate = "%s.0" % self.filename
        if (exists(candidate) and
            exists("%s.1.gz" % self.filename) and
                (stat(candidate).st_mtime >
                 stat("%s.1.gz" % self.filename).st_mtime)):
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


def main():
    if not exists(options.inputfile):
        print('no file found')
        return
    if options.output == 'syslog':
        logger = logging.getLogger()
        logger.addHandler(SysLogHandler(address=(options.sysloghostname, options.syslogport), facility='local4'))
    ptlines = 0

    pt = Pygtail(options.inputfile, options.offsetfile, pretend=False)
    for line in pt:
        if 'TCP_DENIED' in line: 
            mdEvent = MozDefEvent(options.url)
            mdEvent.debug = False
            mdEvent.fire_and_forget_mode = False
            # read and make a log record
            log = createLogRecord(line)
            # http post/syslog/stdout    
            mdEvent.send(timestamp=log['timestamp'], 
                         summary=log['summary'],
                         category=log['category'],
                         severity=log['severity'], 
                         tags=['squid'],
                         details=log['details']
                         )
    pt._update_offset_file()


def getConfig(optionname, thedefault, configfile):
    """read an option from a config file or set a default
       send 'thedefault' as the data class you want to get a string back
       i.e. 'True' will return a string
       True will return a bool
       1 will return an int
    """
    retvalue = thedefault
    opttype = type(thedefault)
    if os.path.isfile(configfile):
        config = ConfigParser.ConfigParser()
        config.readfp(open(configfile))
        if config.has_option('options', optionname):
            if opttype == bool:
                retvalue = config.getboolean('options', optionname)
            elif opttype == int:
                retvalue = config.getint('options', optionname)
            elif opttype == float:
                retvalue = config.getfloat('options', optionname)
            else:
                retvalue = config.get('options', optionname)
    return retvalue


def initConfig(configfile):
    # default options
    options.format = getConfig('format', 'text', configfile)
    options.inputfile = getConfig('inputfile', '', configfile)
    options.output = getConfig('output', 'stdout', configfile)
    options.sysloghostname = getConfig('sysloghostname', 'localhost', configfile)
    options.syslogport = getConfig('syslogport', 514, configfile)
    options.offsetfile = getConfig('offsetfile', 'offset.offset', configfile)
    options.url = getConfig('url', 'http://localhost:8080/events', configfile)

if __name__ == '__main__':
    parser = OptionParser()
    parser.add_option("-c", dest='configfile', default=sys.argv[0].replace('.py', '.conf'), help="configuration file to use")
    (options, args) = parser.parse_args()
    initConfig(options.configfile)
    main()
