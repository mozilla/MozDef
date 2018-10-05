#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
# Copyright (c) 2014 Mozilla Corporation

import copy
import os
import sys
import re
import json
import csv
import string
import ConfigParser
import tempfile
import logging
import socket
import hashlib
import MySQLdb
from requests import Session
from optparse import OptionParser
from datetime import datetime
from os import stat
from os.path import exists, getsize

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
    verify_certificate = False
    # Never fail (ie no unexcepted exceptions sent to user, such as server/network not responding)
    fire_and_forget_mode = True
    log = {}
    log['timestamp'] = datetime.isoformat(datetime.now())
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

        try:
            r = self.httpsession.post(self.url, json.dumps(log_msg, encoding='utf-8'), verify=self.verify_certificate)

        except Exception as e:
            if not self.fire_and_forget_mode:
                raise e


def main():
    '''
    connect to vidyo's mysql, read in calls and write to mozdef
    '''
    mdEvent = MozDefEvent(options.url)
    mdEvent.debug = True
    mdEvent.fire_and_forget_mode = False

    #connect to mysql
    db=MySQLdb.connect(host=options.hostname, user=options.username,passwd=options.password,db=options.database)
    c=db.cursor(MySQLdb.cursors.DictCursor)
    
    c.execute("select * from ConferenceCall2 where JoinTime between NOW() - INTERVAL 30 MINUTE and NOW() or LeaveTime between NOW() - INTERVAL 30 MINUTE and NOW()")
    rows=c.fetchall()
    c.close()
    
    # Build dictionary of calls in order to consolidate multiple rows for a single call
    calls = {}
    for row in rows:
        id = row['UniqueCallID']
        # Copy the row's info if we don't already have the final completed call state
        if id not in calls or (id in calls and  calls[id]['CallState'] != 'COMPLETED'):
            calls[id] = row

    # Massage call data and send to MozDef
    for key in calls.keys():
        call = calls[key]
        if call['LeaveTime'] is not None:
            duration = call['LeaveTime'] - call['JoinTime']
            call['CallDuration'] = duration.seconds

        #fix up the data for json
        for k in call.keys():
            # convert datetime objects to isoformat for json serialization
            if isinstance(call[k], datetime):
                call[k] = call[k].isoformat()
            # make sure it's a string, not unicode forced into a string            
            if isinstance(call[k],str):
                # db has unicode stored as string, so decode, then encode
                call[k] = call[k].decode('utf-8','ignore').encode('ascii','ignore')
        
        mdEvent.send(timestamp=call['JoinTime'],
                     summary='Vidyo call status for '+call['UniqueCallID'].encode('ascii', 'ignore'),
                     tags=['vidyo'],
                     details=call,
                     category='vidyo',
                     hostname=socket.gethostname()
                     )

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
    options.url = getConfig('url', 'http://localhost:8080/events', configfile)
    options.username = getConfig('username', '', configfile)
    options.password = getConfig('password', '', configfile)
    options.database = getConfig('database', '', configfile)
    options.hostname = getConfig('hostname', '', configfile)


if __name__ == '__main__':
    parser = OptionParser()
    parser.add_option("-c", dest='configfile', default=sys.argv[0].replace('.py', '.conf'), help="configuration file to use")
    (options, args) = parser.parse_args()
    initConfig(options.configfile)
    main()
