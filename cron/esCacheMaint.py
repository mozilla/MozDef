#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
# Copyright (c) 2014 Mozilla Corporation

import json
import logging
import pytz
import random
import requests
import sys
import time
from configlib import getConfig, OptionParser
from datetime import datetime, date, timedelta
from dateutil.parser import parse
from elasticsearch import Elasticsearch
logger = logging.getLogger(sys.argv[0])

def loggerTimeStamp(self, record, datefmt=None):
    return datetime.utcnow().isoformat()

def initLogger():
    logger.level = logging.INFO
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    formatter.formatTime = loggerTimeStamp
    sh = logging.StreamHandler(sys.stderr)
    sh.setFormatter(formatter)
    logger.addHandler(sh)

def esConnect(conn):
    '''open or re-open a connection to elastic search'''
    return Elasticsearch((options.esservers))


def isJVMMemoryHigh():
    url = "http://{0}/_nodes/stats?pretty=true".format(random.choice(options.esservers))
    #r=requests.get(url="http://mozdefes5.private.scl3.mozilla.com:9200/_nodes/stats?pretty=true")
    r = requests.get(url)
    logger.debug(r)
    if r.status_code == 200:
        nodestats=r.json()
        #logger.debug(json.dumps(nodestats, indent=4, sort_keys=True))

        for node in nodestats['nodes']:
            loadaverage=nodestats['nodes'][node]['os']['cpu']['load_average']
            cpuusage=nodestats['nodes'][node]['os']['cpu']['percent']
            nodename=nodestats['nodes'][node]['name']
            jvmused=nodestats['nodes'][node]['jvm']['mem']['heap_used_percent']
            logger.debug('{0}: cpu {1}%  jvm {2}% load average: {3}'.format(nodename,cpuusage,jvmused,loadaverage))
            if jvmused> options.jvmlimit:
                logger.info('{0}: cpu {1}%  jvm {2}% load average: {3} recommending cache clear'.format(nodename,cpuusage,jvmused,loadaverage))
                return True
        return False
    else:
        logger.error(r)
        return False

def clearESCache():
    es=esConnect(None)
    indexes=es.indices.stats()['indices']
    # assums index names  like events-YYYYMMDD etc.
    # used to avoid operating on current indexes
    dtNow = datetime.utcnow()
    indexSuffix = date.strftime(dtNow, '%Y%m%d')
    previousSuffix = date.strftime(dtNow - timedelta(days=1), '%Y%m%d')
    for targetindex in sorted(indexes.keys()):
        if indexSuffix not in targetindex and previousSuffix not in targetindex:
            url = 'http://{0}/{1}/_stats'.format(random.choice(options.esservers), targetindex)
            r = requests.get(url)
            if r.status_code == 200:
                indexstats = json.loads(r.text)
                if indexstats['_all']['total']['search']['query_current'] == 0:
                    fielddata = indexstats['_all']['total']['fielddata']['memory_size_in_bytes']
                    if fielddata > 0:
                        logger.info('target: {0}: field data {1}'.format(targetindex, indexstats['_all']['total']['fielddata']['memory_size_in_bytes']))
                        clearurl = 'http://{0}/{1}/_cache/clear'.format(random.choice(options.esservers), targetindex)
                        clearRequest = requests.post(clearurl)
                        logger.info(clearRequest.text)
                        # stop at one?
                        if options.conservative:
                            return
                else:
                    logger.debug('{0}: <ignoring due to current search > field data {1}'.format(targetindex, indexstats['_all']['total']['fielddata']['memory_size_in_bytes']))
            else:
                logger.error('{0} returned {1}'.format(url, r.status_code))

def main():
    if options.checkjvmmemory:
        if isJVMMemoryHigh():
            logger.info('initiating cache clearing')
            clearESCache()
    else:
        clearESCache()

def initConfig():
    # elastic search servers
    options.esservers = list('{0}'.format(s) for s in getConfig('esservers', 'http://localhost:9200', options.configfile).split(','))

    # memory watermark, set to 90 (percent) by default
    options.jvmlimit = getConfig('jvmlimit', 90, options.configfile)

    # be conservative? if set only clears cache for the first index found with no searches and cached field data
    # if false, will continue to clear for any index not matching the date suffix.
    options.conservative = getConfig('conservative', True, options.configfile)

    #check jvm memory first? or just clear cache
    options.checkjvmmemory = getConfig('checkjvmmemory', True, options.configfile)


if __name__ == '__main__':
    # configure ourselves
    parser = OptionParser()
    parser.add_option("-c", dest='configfile', default=sys.argv[0].replace('.py', '.conf'), help="configuration file to use")
    (options, args) = parser.parse_args()
    initConfig()
    initLogger()
    logger.debug('starting')

    main()
