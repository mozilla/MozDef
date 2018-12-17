#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
# Copyright (c) 2014 Mozilla Corporation


import logging
import requests
import sys
from datetime import datetime
from configlib import getConfig, OptionParser
from logging.handlers import SysLogHandler
from pymongo import MongoClient

from mozdef_util.utilities.toUTC import toUTC
from mozdef_util.elasticsearch_client import ElasticsearchClient
from mozdef_util.query_models import SearchQuery, TermMatch

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
                address=(
                    options.sysloghostname,
                    options.syslogport
                )
            )
        )
    else:
        sh = logging.StreamHandler(sys.stderr)
        sh.setFormatter(formatter)
        logger.addHandler(sh)


def getFrontendStats(es):
    search_query = SearchQuery(minutes=15)
    search_query.add_must([
        TermMatch('_type', 'mozdefhealth'),
        TermMatch('category', 'mozdef'),
        TermMatch('tags', 'latest'),
    ])
    results = search_query.execute(es, indices=['mozdefstate'])

    return results['hits']


def writeFrontendStats(data, mongo):
    # Empty everything before
    mongo.healthfrontend.remove({})
    for host in data:
        for key in host['_source']['details'].keys():
            # remove unwanted data
            if '.' in key:
                del host['_source']['details'][key]
        mongo.healthfrontend.insert(host['_source'])


def getSqsStats(es):
    search_query = SearchQuery(minutes=15)
    search_query.add_must([
        TermMatch('_type', 'mozdefhealth'),
        TermMatch('category', 'mozdef'),
        TermMatch('tags', 'sqs-latest'),
    ])
    results = search_query.execute(es, indices=['mozdefstate'])

    return results['hits']


def writeSqsStats(data, mongo):
    # Empty everything before
    mongo.sqsstats.remove({})
    for host in data:
        for key in host['_source']['details'].keys():
            # remove unwanted data
            if '.' in key:
                del host['_source']['details'][key]
        mongo.sqsstats.insert(host['_source'])


def writeEsClusterStats(data, mongo):
    # Empty everything before
    mongo.healthescluster.remove({})
    mongo.healthescluster.insert(data)


def getEsNodesStats():
    r = requests.get(options.esservers[0] + '/_nodes/stats/os,jvm,fs')
    jsonobj = r.json()
    results = []
    for nodeid in jsonobj['nodes']:
        # Skip non masters and non data nodes since it won't have full stats
        if ('attributes' in jsonobj['nodes'][nodeid] and
                jsonobj['nodes'][nodeid]['attributes']['master'] == 'false' and
                jsonobj['nodes'][nodeid]['attributes']['data'] == 'false'):
            continue

        load_average = jsonobj['nodes'][nodeid]['os']['cpu']['load_average']
        load_str = "{0},{1},{2}".format(load_average['1m'], load_average['5m'], load_average['15m'])
        hostname = nodeid
        if 'host' in jsonobj['nodes'][nodeid]:
            hostname=jsonobj['nodes'][nodeid]['host']
        results.append({
            'hostname': hostname,
            'disk_free': jsonobj['nodes'][nodeid]['fs']['total']['free_in_bytes'] / (1024 * 1024 * 1024),
            'disk_total': jsonobj['nodes'][nodeid]['fs']['total']['total_in_bytes'] / (1024 * 1024 * 1024),
            'mem_heap_per': jsonobj['nodes'][nodeid]['jvm']['mem']['heap_used_percent'],
            'gc_old': jsonobj['nodes'][nodeid]['jvm']['gc']['collectors']['old']['collection_time_in_millis'] / 1000,
            'cpu_usage': jsonobj['nodes'][nodeid]['os']['cpu']['percent'],
            'load': load_str
        })
    return results


def writeEsNodesStats(data, mongo):
    # Empty everything before
    mongo.healthesnodes.remove({})
    for nodedata in data:
        mongo.healthesnodes.insert(nodedata)


def getEsHotThreads():
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

    es = ElasticsearchClient((list('{0}'.format(s) for s in options.esservers)))
    client = MongoClient(options.mongohost, options.mongoport)
    # use meteor db
    mongo = client.meteor
    writeFrontendStats(getFrontendStats(es), mongo)
    writeSqsStats(getSqsStats(es), mongo)
    writeEsClusterStats(es.get_cluster_health(), mongo)
    writeEsNodesStats(getEsNodesStats(), mongo)
    writeEsHotThreads(getEsHotThreads(), mongo)


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
