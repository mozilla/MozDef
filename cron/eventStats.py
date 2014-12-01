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
import sys
from datetime import datetime
from datetime import timedelta
from configlib import getConfig, OptionParser
from logging.handlers import SysLogHandler
from dateutil.parser import parse

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


def esSearch(es, begindateUTC=None, enddateUTC=None):
    resultsList = list()
    if begindateUTC is None:
        begindateUTC = toUTC(datetime.now() - timedelta(minutes=options.aggregationminutes))
    if enddateUTC is None:
        enddateUTC = toUTC(datetime.now())
    try:
        # search for events within the date range that haven't already been alerted (i.e. given an alerttimestamp)
        qDate = pyes.RangeQuery(qrange=pyes.ESRange('utctimestamp', from_value=begindateUTC, to_value=enddateUTC))
        q = pyes.ConstantScoreQuery(pyes.MatchAllQuery())
        q = pyes.FilteredQuery(q,pyes.BoolFilter(must=[qDate]))
        
        q=q.search()
        
        qagg = pyes.aggs.TermsAgg(name='category', field='category')
        q.agg.add(qagg)
        results=es.search(query=q,indices=['events'])
        
        mozdefstats=dict(utctimestamp=toUTC(datetime.now()).isoformat())
        mozdefstats['summary']='Aggregated category counts'
        mozdefstats['processid']=os.getpid()
        mozdefstats['processname']=sys.argv[0]
        mozdefstats['details']=dict(counts=list())
        for bucket in results.aggs['category']['buckets']:
            entry=dict()
            entry[bucket['key']]=bucket['doc_count']
            mozdefstats['details']['counts'].append(entry)
        return mozdefstats

    except pyes.exceptions.NoServerAvailable:
        logger.error('Elastic Search server could not be reached, check network connectivity')


def main():
    '''
    Get aggregated statistics on incoming events
    to use in alerting/notices/queries about event patterns over time
    '''
    logger.debug('starting')
    logger.debug(options)
    es = pyes.ES(server=(list('{0}'.format(s) for s in options.esservers)))
    stats = esSearch(es)
    logger.debug(json.dumps(stats))
    try:
        # post to elastic search servers directly without going through
        # message queues in case there is an availability issue
        es.index(index='events',
                 doc_type='mozdefstats',
                 doc=json.dumps(stats),
                 bulk=False)

    except Exception as e:
        logger.error("Exception %r when gathering statistics " % e)

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
    
    # field to use as the aggegation point (category, _type, etc)
    options.aggregationfield = getConfig('aggregationfield',
                                         'category',
                                         options.configfile)

    # default time period in minutes to look back in time for the aggregation
    options.aggregationminutes = getConfig('aggregationminutes',
                                         15,
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
