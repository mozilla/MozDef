#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
# Copyright (c) 2014 Mozilla Corporation
#
# Contributors:
# Jeff Bryner jbryner@mozilla.com

import json
import logging
import os
import pyes
import pytz
import re
import sys
from datetime import datetime
from datetime import timedelta
from configlib import getConfig, OptionParser
from logging.handlers import SysLogHandler
from dateutil.parser import parse
from hashlib import md5

logger = logging.getLogger(sys.argv[0])


def loggerTimeStamp(self, record, datefmt=None):
    return toUTC(datetime.now()).isoformat()


def initLogger():
    logger.level = logging.INFO
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    formatter.formatTime = loggerTimeStamp
    if options.output == 'syslog':
        logger.addHandler(
            SysLogHandler(address=(options.sysloghostname,
                                   options.syslogport)))
    else:
        sh = logging.StreamHandler(sys.stderr)
        sh.setFormatter(formatter)
        logger.addHandler(sh)


def toUTC(suspectedDate, localTimeZone=None):
    '''make a UTC date out of almost anything'''
    utc = pytz.UTC
    objDate = None
    if localTimeZone is None:
        localTimeZone=options.defaulttimezone
    if type(suspectedDate) == str:
        objDate = parse(suspectedDate, fuzzy=True)
    elif type(suspectedDate) == datetime:
        objDate = suspectedDate

    if objDate.tzinfo is None:
        objDate = pytz.timezone(localTimeZone).localize(objDate)
        objDate = utc.normalize(objDate)
    else:
        objDate = utc.normalize(objDate)
    if objDate is not None:
        objDate = utc.normalize(objDate)

    return objDate


def getDocID(usermacaddress):
    # create a hash to use as the ES doc id
    hash = md5()
    hash.update('{0}.mozdefintel.usernamemacaddress'.format(usermacaddress))
    return hash.hexdigest()


def readOUIFile(ouifilename):
    '''
    Expects the OUI file from IEEE:
    wget http://www.ieee.org/netstorage/standards/oui.txt
    Reads the (hex) line and extracts the hex prefix and the vendor name
    to store as part of the intelligence record about what device the user
    was seen using.
    '''
    ouifile=open(ouifilename)
    macassignments={}
    for i in ouifile.readlines()[0::]:
        i=i.strip()
        if '(hex)' in i:
            #print(i)
            fields=i.split('\t')
            macprefix=fields[0][0:8].replace('-',':').lower()
            entity=fields[2]
            macassignments[macprefix]=entity
    return macassignments


def esSearch(es, macassignments=None, begindateUTC=None, enddateUTC=None):
    '''
    Search ES for an event that ties a username to a mac address
    This example searches for junos wifi correlations on authentication success
    Expecting an event like: user: username@somewhere.com; mac: 5c:f9:38:b1:de:cf; author reason: roamed session; ssid: ANSSID; AP 46/2\n
    '''
    usermacre=re.compile(r'''user: (?P<username>.*?); mac: (?P<macaddress>.*?); ''',re.IGNORECASE)
    correlations={} # list of dicts to populate hits we find

    if begindateUTC is None:
        begindateUTC = toUTC(datetime.now() - timedelta(minutes=options.correlationminutes))
    if enddateUTC is None:
        enddateUTC = toUTC(datetime.now())
    try:
        # search for events within the date range
        qDate = pyes.RangeQuery(qrange=pyes.ESRange('utctimestamp', from_value=begindateUTC, to_value=enddateUTC))
        q=pyes.ConstantScoreQuery(pyes.MatchAllQuery())
        q.filters.append(pyes.BoolFilter(must=[ 
                                               qDate,
                                               pyes.TermFilter("program","AUTHORIZATION-SUCCESS")
                                               ],
                                         must_not=[
                                                    pyes.QueryFilter(
                                                        pyes.MatchQuery("summary","last-resort","phrase")
                                                    )
                                                   ]))
        results = es.search(q, size=10000, indices=['events', 'events-previous'])
        rawresults=results._search_raw()

        for r in rawresults['hits']['hits']:
            fields = re.search(usermacre,r['_source']['summary'])
            if fields:
                if '{0} {1}'.format(fields.group('username'),fields.group('macaddress')) not in correlations.keys():
                    if fields.group('macaddress')[0:8].lower() in macassignments.keys():
                        entity=macassignments[fields.group('macaddress')[0:8].lower()]
                    else:
                        entity='unknown'
                    correlations['{0} {1}'.format(fields.group('username'),fields.group('macaddress'))]=dict(username=fields.group('username'),
                                                                                                             macaddress=fields.group('macaddress'),
                                                                                                             entity=entity,
                                                                                                             utctimestamp=r['_source']['utctimestamp'])
        return correlations
        
    except pyes.exceptions.NoServerAvailable:
        logger.error('Elastic Search server could not be reached, check network connectivity')

def esStoreCorrelations(es, correlations):
    for c in correlations:
        event=dict(
                   utctimestamp=correlations[c]['utctimestamp'],
                   summary=c,
                   details=dict(
                       username=correlations[c]['username'],
                       macaddress=correlations[c]['macaddress'],
                       entity=correlations[c]['entity']
                       ),
                   category='indicators'
                   )
        try:
            es.index(index='intelligence',
                     id=getDocID(c),
                     doc_type='usernamemacaddress',
                     doc=json.dumps(event),
                     bulk=False)
        except Exception as e:
            logger.error("Exception %r when posting correlation " % e)        


def main():
    '''
    Look for events that contain username and a mac address
    Add the correlation to the intelligence index.
    '''
    logger.debug('starting')
    logger.debug(options)

    es = pyes.ES(server=(list('{0}'.format(s) for s in options.esservers)))
    # create intelligence index if it's not already there
    es.indices.create_index_if_missing('intelligence',dict(number_of_shards=2,number_of_replicas=1))    
    
    # read in the OUI file for mac prefix to vendor dictionary
    macassignments = readOUIFile(options.ouifilename)
    
    # search ES for events containing username and mac address
    correlations = esSearch(es, macassignments=macassignments)
    
    # store the correlation in the intelligence index
    esStoreCorrelations(es, correlations)

    logger.debug('finished')


def initConfig():
    # output our log to stdout or syslog
    options.output = getConfig('output', 'stdout', options.configfile)
    # syslog hostname
    options.sysloghostname = getConfig('sysloghostname',
                                       'localhost',
                                       options.configfile)
    # syslog port
    options.syslogport = getConfig('syslogport', 514, options.configfile)


    # change this to your default zone for when it's not specified
    options.defaulttimezone = getConfig('defaulttimezone',
                                        'UTC',
                                        options.configfile)

    # elastic search server settings
    options.esservers = list(getConfig('esservers',
                                       'http://localhost:9200',
                                       options.configfile).split(','))
    

    # default time period in minutes to look back in time for the aggregation
    options.correlationminutes = getConfig('correlationminutes',
                                         150,
                                         options.configfile)
    
    # default location of the OUI file from IEEE for resolving mac prefixes
    # Expects the OUI file from IEEE:
    # wget http://www.ieee.org/netstorage/standards/oui.txt    
    options.ouifilename = getConfig('ouifilename',
                                'oui.txt',
                                options.configfile)



if __name__ == '__main__':
    parser = OptionParser()
    parser.add_option(
        "-c",
        dest='configfile',
        default=sys.argv[0].replace('.py', '.conf'),
        help="configuration file to use")
    (options, args) = parser.parse_args()
    initConfig()
    initLogger()
    main()
