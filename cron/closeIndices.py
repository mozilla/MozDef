#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
# Copyright (c) 2014 Mozilla Corporation

# set this to run as a cronjob (after backup has completed)
# to regularly remove indexes

# .conf file will determine what indexes are operated on
# Create a starter .conf file with backupDiscover.py

import sys
from datetime import datetime, timedelta
from configlib import getConfig, OptionParser

from mozdef_util.utilities.logger import logger
from mozdef_util.utilities.toUTC import toUTC
from mozdef_util.elasticsearch_client import ElasticsearchClient


def esCloseIndices():
    logger.debug('started')
    try:
        es = ElasticsearchClient((list('{0}'.format(s) for s in options.esservers)))
        indices = es.get_indices()
    except Exception as e:
        logger.error("Unhandled exception while connecting to ES, terminating: %r" % (e))

    # examine each index pulled from get_indice
    # to determine if it meets aging criteria
    for index in indices:
        if 'events' in index:
            index_date = index.rsplit('-', 1)[1]
            logger.debug("Checking to see if Index: %s can be closed." % (index))
            month_ago_date = toUTC(datetime.now()) - timedelta(days=options.index_age)
            point_of_close = month_ago_date.strftime('%Y%m%d')
            if len(index_date) == 8:
                month_ago_str = point_of_close
                index_date_obj = datetime.strptime(index_date, '%Y%m%d')
                index_date_str = index_date_obj.strftime('%Y%m%d')
                try:
                    if int(month_ago_str) > int(index_date_str):
                        logger.debug("Index: %s will be closed." % (index))
                        es.index_close(index)
                    else:
                        logger.debug("Index: %s  does not meet aging criteria and will not be closed." % (index_date_str))
                except Exception as e:
                    logger.error("Unhandled exception while closing indices, terminating: %r" % (e))


def initConfig():
    # output our log to stdout or syslog
    options.output = getConfig(
        'output',
        'stdout',
        options.configfile
    )
    # syslog hostname
    options.sysloghostname = getConfig(
        'sysloghostname',
        'localhost',
        options.configfile
    )
    options.syslogport = getConfig(
        'syslogport',
        514,
        options.configfile
    )
    options.esservers = list(getConfig(
        'esservers',
        'http://localhost:9200',
        options.configfile).split(',')
    )
    options.index_age = getConfig(
        'index_age',
        '15',
        options.configfile
    )


if __name__ == '__main__':
    parser = OptionParser()
    parser.add_option("-c",
                      dest='configfile',
                      default=sys.argv[0].replace('.py', '.conf'),
                      help="configuration file to use")
    (options, args) = parser.parse_args()
    initConfig()
    esCloseIndices()
