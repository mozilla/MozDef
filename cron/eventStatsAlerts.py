#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
# Copyright (c) 2014 Mozilla Corporation
#
# Contributors:
# Jeff Bryner jbryner@mozilla.com

import logging
import numpy
import os
import sys
from datetime import datetime
from configlib import getConfig, OptionParser
from logging.handlers import SysLogHandler

import sys
import os
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../lib'))
from utilities.toUTC import toUTC
from elasticsearch_client import ElasticsearchClient, ElasticsearchBadServer
from query_models import SearchQuery, TermMatch


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


def esSearch(es):
    search_query = SearchQuery(minutes=options.aggregationminutes)
    search_query.add_must(TermMatch('_type', 'mozdefstats'))

    try:
        full_results = search_query.execute(es, size=100)
        #examine the results
        #for each details.counts, append the count
        #as a list to the stats dict
        stats=dict()
        for r in full_results['hits']:
            for i in r['_source']['details']['counts']:
                #print(i.values()[0])
                if i.keys()[0] not in stats.keys():
                    stats[i.keys()[0]]=list()
                stats[i.keys()[0]].append(i.values()[0])

        # make a dictionairy of user-defined
        # aggregation threshold percentages
        aggregationthresholds = dict(zip(options.aggregations,
                                         options.aggregationthresholds))

        #for our running history of counts per category
        #do some simple stats math to see if we
        #should alert on anything
        for s in stats:
            alert = False
            smean=round(numpy.mean(stats[s]))
            sstd=round(numpy.std(stats[s]))
            stat = round((sstd/smean)*100, 2)
            if s in aggregationthresholds.keys():
                if stat > aggregationthresholds[s]:
                    alert = True
            elif  stat > options.defaultthreshold:
                alert = True

            if alert:
                print('{0} {1}%: \n\t\t{2} \n\t\t{3} \n\t\t{4}'.format(
                                                s,
                                                stat,
                                                stats[s],
                                                smean,
                                                sstd
                                                )
                      )

    except ElasticsearchBadServer:
        logger.error('Elastic Search server could not be reached, check network connectivity')


def main():
    '''
    Get aggregated statistics on incoming events
    to use in alerting/notices/queries about event patterns over time
    '''
    logger.debug('starting')
    logger.debug(options)
    es = ElasticsearchClient((list('{0}'.format(s) for s in options.esservers)))
    esSearch(es)
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

    # field to use as the aggegation point (category, _type, etc)
    options.aggregationfield = getConfig('aggregationfield',
                                         'category',
                                         options.configfile)

    # default time period in minutes to look back in time for the aggregation
    options.aggregationminutes = getConfig('aggregationminutes',
                                         15,
                                         options.configfile)

    # set the threshold per aggregation to alert
    # use this to customize the std deviation/mean at which an alert is
    # generated
    options.aggregations = list(getConfig('aggregations',
                                         '',
                                         options.configfile
                                         ).split(','))

    options.aggregationthresholds = list(getConfig('aggregationthresholds',
                                         '',
                                         options.configfile
                                         ).split(','))

    # default threshold to use if not specified in the list above
    options.defaultthreshold = getConfig('defaultthreshold',
                                         90,
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
