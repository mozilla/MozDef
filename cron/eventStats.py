#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# Copyright (c) 2014 Mozilla Corporation

import json
import os
import sys
from datetime import datetime
from configlib import getConfig, OptionParser
from time import sleep
import socket

from mozdef_util.utilities.logger import logger
from mozdef_util.utilities.toUTC import toUTC
from mozdef_util.elasticsearch_client import ElasticsearchClient
from mozdef_util.query_models import SearchQuery, Aggregation


def esSearch(es):
    search_query = SearchQuery(minutes=options.aggregationminutes)
    search_query.add_aggregation(Aggregation('category'))
    results = search_query.execute(es)

    mozdefstats = dict(utctimestamp=toUTC(datetime.now()).isoformat())
    mozdefstats['category'] = 'stats'
    mozdefstats['hostname'] = socket.gethostname()
    mozdefstats['mozdefhostname'] = mozdefstats['hostname']
    mozdefstats['type'] = 'mozdefstats'
    mozdefstats['severity'] = 'INFO'
    mozdefstats['source'] = 'mozdef'
    mozdefstats['tags'] = ['mozdef', 'stats']
    mozdefstats['summary'] = 'Aggregated category counts'
    mozdefstats['processid'] = os.getpid()
    mozdefstats['processname'] = sys.argv[0]
    mozdefstats['details'] = dict(counts=list())
    for bucket in results['aggregations']['category']['terms']:
        entry = dict()
        entry[bucket['key']] = bucket['count']
        mozdefstats['details']['counts'].append(entry)
    return mozdefstats


def main():
    '''
    Get aggregated statistics on incoming events
    to use in alerting/notices/queries about event patterns over time
    '''
    logger.debug('starting')
    logger.debug(options)
    es = ElasticsearchClient((list('{0}'.format(s) for s in options.esservers)))
    index = options.index
    stats = esSearch(es)
    logger.debug(json.dumps(stats))
    sleepcycles = 0
    try:
        while not es.index_exists(index):
            sleep(3)
            if sleepcycles == 3:
                logger.debug("The index is not created. Terminating eventStats.py cron job.")
                exit(1)
            sleepcycles += 1
        if es.index_exists(index):
            # post to elastic search servers directly without going through
            # message queues in case there is an availability issue
            es.save_event(index=index, body=json.dumps(stats))

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

    # elastic search server settings
    options.esservers = list(getConfig('esservers',
                                       'http://localhost:9200',
                                       options.configfile).split(','))

    # field to use as the aggegation point (category, type, etc)
    options.aggregationfield = getConfig('aggregationfield',
                                         'category',
                                         options.configfile)

    # default time period in minutes to look back in time for the aggregation
    options.aggregationminutes = getConfig('aggregationminutes',
                                           15,
                                           options.configfile)
    # configure the index to save events to
    options.index = getConfig('index', 'mozdefstate', options.configfile)


if __name__ == '__main__':
    parser = OptionParser()
    parser.add_option(
        "-c",
        dest='configfile',
        default=sys.argv[0].replace('.py', '.conf'),
        help="configuration file to use")
    (options, args) = parser.parse_args()
    initConfig()
    main()
