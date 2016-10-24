#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
# Copyright (c) 2014 Mozilla Corporation
#
# Contributors:
# Jeff Bryner jbryner@mozilla.com

import logging
import random
import sys
from datetime import datetime
from configlib import getConfig, OptionParser
from logging.handlers import SysLogHandler
from pymongo import MongoClient

import sys
import os
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../lib'))
from utilities.toUTC import toUTC
from elasticsearch_client import ElasticsearchClient
from query_models import SearchQuery, TermMatch, PhraseMatch

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


def genMeteorID():
    return('%024x' % random.randrange(16**24))


def searchForSSHKeys(es):
    search_query = SearchQuery(minutes=5)
    search_query.add_must([
        TermMatch('_type', 'event'),
        TermMatch('program', 'sshd'),
        PhraseMatch('summary', 'found matching key accepted publickey')
    ])
    results = search_query.execute(es)
    return results


def correlateSSHKeys(esResults):
    # correlate ssh key to userid by hostname and processid
    # dict to populate hits we find
    # will be a dict with hostname:processid as they key and sshkey and username as the dict items.
    correlations = {}
    # a list for the final dicts containing keys: username and key
    uniqueCorrelations = []

    # first find the keys
    for r in esResults['hits']:
        if 'found matching' in r['_source']['summary'].lower():
            hostname = r['_source']['details']['hostname']
            processid = r['_source']['details']['processid']
            sshkey = r['_source']['summary'].split('key:')[1].strip()
            if '{0}:{1}'.format(hostname, processid) not in correlations.keys():
                correlations['{0}:{1}'.format(hostname, processid)] = dict(sshkey=sshkey)
    # find the users and match on host:processid
    for r in esResults['hits']:
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
        es = ElasticsearchClient((list('{0}'.format(s) for s in options.esservers)))
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
