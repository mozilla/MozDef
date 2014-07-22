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
    logger.level = logging.DEBUG
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


def searchForAttackers(es, threshold):
    begindateUTC = toUTC(datetime.now() - timedelta(minutes=30))
    enddateUTC = toUTC(datetime.now())
    qDate = pyes.RangeQuery(qrange=pyes.ESRange('utctimestamp', from_value=begindateUTC, to_value=enddateUTC))
    q = pyes.ConstantScoreQuery(pyes.MatchAllQuery())
    qBro = pyes.QueryFilter(pyes.MatchQuery('category', 'bro_notice', 'phrase'))
    qErr = pyes.QueryFilter(pyes.MatchQuery('details.note', 'MozillaHTTPErrors::Excessive_HTTP_Errors_Attacker', 'phrase'))
    q = pyes.FilteredQuery(q, pyes.BoolFilter(must=[qBro, qErr]))

    results = es.search(q, size=10, indices='events')
    # grab results as native es results to avoid pyes iteration bug
    # and get easier access to es metadata fields
    rawresults = results._search_raw()['hits']['hits']
    
    # Hit count is buried in the 'sub' field
    # as: 'sub': u'6 in 1.0 hr, eps: 0'
    # cull the records for hitcounts over the threshold before returning
    attackers = list()
    for r in rawresults:
        hitcount = int(r['_source']['details']['sub'].split()[0])
        if hitcount > threshold:
            attackers.append(r)
    return attackers


def genNewAttacker():
    newAttacker = dict()
    newAttacker['_id'] = genMeteorID()
    newAttacker['lastseentimestamp'] = toUTC(datetime.now())
    newAttacker['firstseentimestamp'] = toUTC(datetime.now())
    newAttacker['events'] = list()
    newAttacker['eventscount'] = 0
    newAttacker['alerts'] = list()
    newAttacker['alertscount'] = 0
    newAttacker['category'] = 'unknown'
    newAttacker['score'] = 0
    newAttacker['geocoordinates'] = dict(countrycode='', longitude=0, lattitude=0)
    newAttacker['tags'] = list()
    newAttacker['notes'] = list()
    newAttacker['attackphase'] = 'unknown'
    return newAttacker

def updateMongo(mozdefdb, results):
    attackers=mozdefdb['attackers']
    for r in results:
        if 'sourceipaddress' in r['_source']['details']:
            if netaddr.valid_ipv4(r['_source']['details']['sourceipaddress']):
                sourceIP = netaddr.IPNetwork(r['_source']['details']['sourceipaddress'])[0]
                if not sourceIP.is_loopback() and not sourceIP.is_private() and not sourceIP.is_reserved():
                    esrecord = r['_source']
                    logger.debug('searching for ' + str(sourceIP))
                    attacker = attackers.find_one({'events.details.sourceipaddress': str(sourceIP)})
                    if attacker is None:
                        # new attacker
                        # generate a meteor-compatible ID
                        # save the ES document type, index, id
                        # and add a sub list for future events
                        logger.debug('new attacker')
                        newAttacker = genNewAttacker()
                        esrecord['es_id'] = r['_id']
                        esrecord['es_type'] = r['_type']
                        esrecord['es_index'] = r['_index']                        
                        newAttacker['events'].append(esrecord)

                        attackers.insert(newAttacker)
                    else:
                        # if event not present in this attackers events
                        # append this to the list of events
                        # todo: trim the list at X (i.e. last 100 events)
                        matchingevent = attackers.find_one(
                            {'_id': attacker['_id'],
                             'events.es_id': r['_id'],
                             'events.es_type': r['_type'],
                             'events.es_index': r['_index']
                             })
                        if matchingevent is None: 
                            esrecord['es_id'] = r['_id']
                            esrecord['es_type'] = r['_type']
                            esrecord['es_index'] = r['_index']
                            attacker['events'].append(esrecord)
                            attacker['eventscount'] = len(attacker['events'])
                            logger.debug('new event found for matching attacker')
                            attackers.save(attacker)


def main():
    logger.debug('starting')
    logger.debug(options)
    try:
        es = pyes.ES(server=(list('{0}'.format(s) for s in options.esservers)))
        client = MongoClient(options.mongohost, options.mongoport)
        # use meteor db
        mozdefdb = client.meteor
        results = searchForAttackers(es, 5)
        updateMongo(mozdefdb, results)

    except Exception as e:
        logger.error("Exception %r collecting attackers to mongo" % e)


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
