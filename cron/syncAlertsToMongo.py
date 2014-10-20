#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
# Copyright (c) 2014 Mozilla Corporation
#
# Contributors:
# Jeff Bryner jbryner@mozilla.com

import calendar
import logging
import pyes
import pytz
import random
import netaddr
import sys
from datetime import datetime
from datetime import timedelta
from configlib import getConfig, OptionParser
from logging.handlers import SysLogHandler
from dateutil.parser import parse
from pymongo import MongoClient
from pymongo import collection

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
            SysLogHandler(
                address=(options.sysloghostname, options.syslogport)))
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
    if type(suspectedDate) in (str, unicode):
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


def genMeteorID():
    return('%024x' % random.randrange(16**24))


def getESAlerts(es):
    begindateUTC = toUTC(datetime.now() - timedelta(minutes=50))
    enddateUTC = toUTC(datetime.now())
    qDate = pyes.RangeQuery(qrange=pyes.ESRange('utctimestamp',
                                                from_value=begindateUTC,
                                                to_value=enddateUTC))
    qType = pyes.TermFilter('_type', 'alert')
    q = pyes.ConstantScoreQuery(pyes.MatchAllQuery())
    q.filters.append(pyes.BoolFilter(must=[qDate, qType]))
    results = es.search(q, size=10000, indices='alerts')
    # return raw search to avoid pyes iteration bug
    return results._search_raw()


def ensureIndexes(mozdefdb):
    '''
    make sure we've got or create
    1) an index on the utcepoch field in descending order
       to make it easy on the alerts screen queries.
    2) an index on esmetadata.id for correlation to ES
    
    '''
    alerts = mozdefdb['alerts']
    alerts.ensure_index([('utcepoch',-1)])
    alerts.ensure_index([('esmetadata.id',1)])
    
def updateMongo(mozdefdb, esAlerts):
    alerts = mozdefdb['alerts']
    for a in esAlerts['hits']['hits']:
        # insert alert into mongo if we don't already have it
        alertrecord = alerts.find_one({'esmetadata.id': a['_id']})
        if alertrecord is None:
            # new record
            mrecord = a['_source']
            # generate a meteor-compatible ID
            mrecord['_id'] = genMeteorID()
            # capture the elastic search meta data (index/id/doctype)
            # set the date back to a datetime from unicode, so mongo/meteor can properly sort, select. 
            mrecord['utctimestamp']=toUTC(mrecord['utctimestamp'],'UTC')
            # also set an epoch time field so minimongo can sort
            mrecord['utcepoch'] = calendar.timegm(mrecord['utctimestamp'].utctimetuple())
            mrecord['esmetadata'] = dict()
            mrecord['esmetadata']['id'] = a['_id']
            mrecord['esmetadata']['index'] = a['_index']
            mrecord['esmetadata']['type'] = a['_type']
            alerts.insert(mrecord)


def main():
    logger.debug('starting')
    logger.debug(options)
    try:
        es = pyes.ES(server=(list('{0}'.format(s) for s in options.esservers)))
        client = MongoClient(options.mongohost, options.mongoport)
        mozdefdb = client.meteor
        ensureIndexes(mozdefdb)
        esResults = getESAlerts(es)
        updateMongo(mozdefdb, esResults)

    except Exception as e:
        logger.error("Exception %r sending health to mongo" % e)


def initConfig():
    #change this to your default timezone
    options.defaulttimezone=getConfig('defaulttimezone','UTC',options.configfile)    
    # output our log to stdout or syslog
    options.output = getConfig('output', 'stdout', options.configfile)
    # syslog hostname
    options.sysloghostname = getConfig('sysloghostname',
                                       'localhost',
                                       options.configfile)
    # syslog port
    options.syslogport = getConfig('syslogport', 514, options.configfile)

    # elastic search server settings
    options.esservers = list(getConfig('esservers',
                                       'http://localhost:9200',
                                       options.configfile).split(','))
    options.mongohost = getConfig('mongohost', 'localhost', options.configfile)
    options.mongoport = getConfig('mongoport', 3001, options.configfile)


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
