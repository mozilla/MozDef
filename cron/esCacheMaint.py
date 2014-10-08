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
import math
import pyes
import pytz
import random
import requests
import sys
import time
from configlib import getConfig, OptionParser
from datetime import datetime, date, timedelta
from dateutil.parser import parse
logger = logging.getLogger(sys.argv[0])


def loggerTimeStamp(self, record, datefmt=None):
    return toUTC(datetime.now()).isoformat()


def initLogger():
    logger.level = logging.INFO
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    formatter.formatTime = loggerTimeStamp
    sh = logging.StreamHandler(sys.stderr)
    sh.setFormatter(formatter)
    logger.addHandler(sh)


def isNumber(s):
    'check if a token is numeric, return bool'
    try:
        float(s)  # for int, long and float
    except ValueError:
        try:
            complex(s)  # for complex
        except ValueError:
            return False
    return True


def digits(n):
    '''return the number of digits in a number'''
    if n > 0:
        digits = int(math.log10(n))+1
    elif n == 0:
        digits = 1
    else:
        digits = int(math.log10(-n))+2
    return digits


def toUTC(suspectedDate, localTimeZone=None):
    '''make a UTC date out of almost anything'''
    utc = pytz.UTC
    objDate = None
    if localTimeZone is None:
        localTimeZone = options.defaultTimeZone

    if type(suspectedDate) == datetime:
        objDate = suspectedDate
    elif isNumber(suspectedDate):
        # epoch? but seconds/milliseconds/nanoseconds (lookin at you heka)
        epochDivisor = int(str(1) + '0'*(digits(suspectedDate) % 10))
        objDate = datetime.fromtimestamp(float(suspectedDate/epochDivisor))
    elif type(suspectedDate) in (str, unicode):
        objDate = parse(suspectedDate, fuzzy=True)

    if objDate.tzinfo is None:
        objDate = pytz.timezone(localTimeZone).localize(objDate)
        objDate = utc.normalize(objDate)
    else:
        objDate = utc.normalize(objDate)
    if objDate is not None:
        objDate = utc.normalize(objDate)

    return objDate


def esConnect(conn):
    '''open or re-open a connection to elastic search'''
    return pyes.ES(server=(list('{0}'.format(s) for s in options.esservers)))


def isJVMMemoryHigh():
    url = "http://{0}/_nodes/stats?pretty=true".format(random.choice(options.esservers))
    #r=requests.get(url="http://mozdefes5.private.scl3.mozilla.com:9200/_nodes/stats?pretty=true")
    r = requests.get(url)
    logger.debug(r)
    if r.status_code == 200:
        nodestats=r.json()
        #logger.debug(json.dumps(nodestats, indent=4, sort_keys=True))
    
        for node in nodestats['nodes']:
            loadaverage=nodestats['nodes'][node]['os']['load_average']
            cpuusage=nodestats['nodes'][node]['os']['cpu']['usage']
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
    indexes=es.indices.status()['indices']
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
                        if options.conservative:
                            return
                else:
                    logger.debug('{0}: <ignoring due to current search > field data {1}'.format(targetindex, indexstats['_all']['total']['fielddata']['memory_size_in_bytes']))
            else:
                logger.error('{0} returned {1}'.format(url, r.status_code))
    

def main():
    if isJVMMemoryHigh():
        logger.info('initiating cache clearing')
        clearESCache()


def initConfig():
    # change this to your default zone for when it's not specified
    options.defaultTimeZone = getConfig('defaulttimezone', 'US/Pacific', options.configfile)

    # elastic search options.
    options.esservers = list(getConfig('esservers', 'http://localhost:9200', options.configfile).split(','))
    
    # memory watermark, set to 90 (percent) by default
    options.jvmlimit = getConfig('jvmlimit', 90, options.configfile)
    
    # be conservative? if set only clears cache for the first index found with no searches and cached field data
    # if false, will continue to clear for any index not matching the date suffix.
    options.conservative = getConfig('conservative', True, options.configfile)


if __name__ == '__main__':
    # configure ourselves
    parser = OptionParser()
    parser.add_option("-c", dest='configfile', default=sys.argv[0].replace('.py', '.conf'), help="configuration file to use")
    (options, args) = parser.parse_args()
    initConfig()
    initLogger()
    logger.debug('starting')

    main()