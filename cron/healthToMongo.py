#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
# Copyright (c) 2014 Mozilla Corporation
#
# Contributors:
# Anthony Verez averez@mozilla.com

import logging
import pyes
import pytz
import requests
import sys
from datetime import datetime
from datetime import timedelta
from configlib import getConfig, OptionParser
from logging.handlers import SysLogHandler
from dateutil.parser import parse
from pymongo import MongoClient

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
                address=(options.sysloghostname,
                    options.syslogport)))
    else:
        sh = logging.StreamHandler(sys.stderr)
        sh.setFormatter(formatter)
        logger.addHandler(sh)


def toUTC(suspectedDate, localTimeZone="UTC"):
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


def getFrontendStats(es):
    begindateUTC = toUTC(datetime.now() - timedelta(minutes=15), options.defaulttimezone)
    enddateUTC = toUTC(datetime.now(), options.defaulttimezone)
    qDate = pyes.RangeQuery(qrange=pyes.ESRange('utctimestamp',
        from_value=begindateUTC, to_value=enddateUTC))
    qType = pyes.TermFilter('_type', 'mozdefhealth')
    qMozdef = pyes.TermsFilter('category', ['mozdef'])
    qLatest = pyes.TermsFilter('tags', ['latest'])
    pyesresults = es.search(pyes.ConstantScoreQuery(pyes.BoolFilter(
        must=[qDate, qType, qLatest, qMozdef])),
        indices='events')
    return pyesresults._search_raw()['hits']['hits']


def writeFrontendStats(data, mongo):
    # Empty everything before
    mongo.healthfrontend.remove({})
    for host in data:
        for key in host['_source']['details'].keys():
            # remove unwanted data
            if '.' in key:
                del host['_source']['details'][key]
        mongo.healthfrontend.insert(host['_source'])


def getEsClusterStats(es):
    escluster = pyes.managers.Cluster(es)
    return escluster.health()


def writeEsClusterStats(data, mongo):
    # Empty everything before
    mongo.healthescluster.remove({})
    mongo.healthescluster.insert(data)


def getEsNodesStats():
    # doesn't work with pyes
    r = requests.get(options.esservers[0] + '/_nodes/stats/os,jvm,fs')
    jsonobj = r.json()
    results = []
    for nodeid in jsonobj['nodes']:
        results.append({
            'hostname': jsonobj['nodes'][nodeid]['host'],
            'disk_free': jsonobj['nodes'][nodeid]['fs']['total']['free_in_bytes'] / (1024 * 1024 * 1024),
            'disk_total': jsonobj['nodes'][nodeid]['fs']['total']['total_in_bytes'] / (1024 * 1024 * 1024),
            'mem_heap_per': jsonobj['nodes'][nodeid]['jvm']['mem']['heap_used_percent'],
            'cpu_usage': jsonobj['nodes'][nodeid]['os']['cpu']['usage'],
            'load': jsonobj['nodes'][nodeid]['os']['load_average']
        })
    return results


def writeEsNodesStats(data, mongo):
    # Empty everything before
    mongo.healthesnodes.remove({})
    for nodedata in data:
        mongo.healthesnodes.insert(nodedata)


def getEsHotThreads():
    # doesn't work with pyes
    r = requests.get(options.esservers[0] + '/_nodes/hot_threads')
    results = []
    for line in r.text.split('\n'):
        if 'cpu usage' in line:
            results.append(line)
    return results


def writeEsHotThreads(data, mongo):
    # Empty everything before
    mongo.healtheshotthreads.remove({})
    for line in data:
        mongo.healtheshotthreads.insert({'line': line})


def main():
    logger.debug('starting')
    logger.debug(options)
    try:
        es = pyes.ES(server=(list('{0}'.format(s) for s in options.esservers)))
        client = MongoClient(options.mongohost, options.mongoport)
        # use meteor db
        mongo = client.meteor
        writeFrontendStats(getFrontendStats(es), mongo)
        writeEsClusterStats(getEsClusterStats(es), mongo)
        writeEsNodesStats(getEsNodesStats(), mongo)
        writeEsHotThreads(getEsHotThreads(), mongo)
    except Exception as e:
        logger.error("Exception %r sending health to mongo" % e)


def initConfig():
    # output our log to stdout or syslog
    options.output = getConfig('output', 'stdout', options.configfile)
    # syslog hostname
    options.sysloghostname = getConfig('sysloghostname', 'localhost',
        options.configfile)
    # syslog port
    options.syslogport = getConfig('syslogport', 514, options.configfile)

    # elastic search server settings
    options.esservers = list(getConfig('esservers', 'http://localhost:9200',
        options.configfile).split(','))
    options.mongohost = getConfig('mongohost', 'localhost', options.configfile)
    options.mongoport = getConfig('mongoport', 3001, options.configfile)
    # change this to your default zone for when it's not specified
    options.defaulttimezone = getConfig('defaulttimezone',
                                        'UTC',
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

