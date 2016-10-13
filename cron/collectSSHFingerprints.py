#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
# Copyright (c) 2014 Mozilla Corporation
#
# Contributors:
# Jeff Bryner jbryner@mozilla.com

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
import re
userre = re.compile(r'''Accepted publickey for (.*?) from''', re.IGNORECASE)


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


def toUTC(suspectedDate, localTimeZone="US/Pacific"):
    '''make a UTC date out of almost anything'''
    utc = pytz.UTC
    objDate = None
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


def genMeteorID():
    return('%024x' % random.randrange(16**24))


def searchForSSHKeys(es):
    begindateUTC = toUTC(datetime.now() - timedelta(minutes=5))
    enddateUTC = toUTC(datetime.now())
    qDate = pyes.RangeQuery(qrange=pyes.ESRange('utctimestamp',
                                                from_value=begindateUTC,
                                                to_value=enddateUTC))
    qType = pyes.TermFilter('_type', 'event')
    qEvents = pyes.TermFilter("program", "sshd")
    q = pyes.ConstantScoreQuery(pyes.MatchAllQuery())
    q.filters.append(
        pyes.BoolFilter(must=[qType,
                              qDate,
                              qEvents,
                              pyes.QueryFilter(
                                  pyes.MatchQuery("summary",
                                                  "found matching key accepted publickey",
                                                  "boolean"))
                              ]))

    results = es.search(q, size=10000, indices='events')
    # return raw search to avoid pyes iteration bug
    return results._search_raw()


def correlateSSHKeys(esResults):
    # correlate ssh key to userid by hostname and processid
    # dict to populate hits we find
    # will be a dict with hostname:processid as they key and sshkey and username as the dict items.
    correlations = {}
    # a list for the final dicts containing keys: username and key
    uniqueCorrelations = []

    # first find the keys
    for r in esResults['hits']['hits']:
        if 'found matching' in r['_source']['summary'].lower():
            hostname = r['_source']['details']['hostname']
            processid = r['_source']['details']['processid']
            sshkey = r['_source']['summary'].split('key:')[1].strip()
            if '{0}:{1}'.format(hostname, processid) not in correlations.keys():
                correlations['{0}:{1}'.format(hostname, processid)] = dict(sshkey=sshkey)
    # find the users and match on host:processid
    for r in esResults['hits']['hits']:
        if 'accepted publickey' in r['_source']['summary'].lower():
            hostname = r['_source']['details']['hostname']
            processid = r['_source']['details']['processid']
            username = userre.split(r['_source']['summary'])[1]
            if '{0}:{1}'.format(hostname, processid) in correlations.keys() and 'username' not in correlations['{0}:{1}'.format(hostname, processid)].keys():
                correlations['{0}:{1}'.format(hostname, processid)]['username'] = username

    for c in correlations:
        if 'username' in correlations[c].keys():
            if correlations[c] not in uniqueCorrelations:
                uniqueCorrelations.append(correlations[c])
    return uniqueCorrelations


def updateMongo(mozdefdb, correlations):
    sshkeys = mozdefdb['sshkeys']
    for c in correlations:
        keyrecord = sshkeys.find_one({'sshkey': c['sshkey']})
        if keyrecord is None:
            # new record
            # generate a meteor-compatible ID
            c['_id'] = genMeteorID()
            c['utctimestamp'] = toUTC(datetime.now()).isoformat()
            logger.debug(c)
            sshkeys.insert(c)


def main():
    logger.debug('starting')
    logger.debug(options)
    try:
        es = pyes.ES(server=(list('{0}'.format(s) for s in options.esservers)))
        client = MongoClient(options.mongohost, options.mongoport)
        # use meteor db
        mozdefdb = client.meteor
        esResults = searchForSSHKeys(es)
        correlations = correlateSSHKeys(esResults)
        if len(correlations) > 0:
            updateMongo(mozdefdb, correlations)

    except Exception as e:
        logger.error("Exception %r sending health to mongo" % e)


def initConfig():
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
