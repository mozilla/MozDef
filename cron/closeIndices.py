#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
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
        indices = es.get_open_indices()
    except Exception as e:
        logger.error("Unhandled exception while connecting to ES, terminating: %r" % (e))

    # examine each index pulled from get_indice
    # to determine if it meets aging criteria
    month_ago_date = toUTC(datetime.now()) - timedelta(days=int(options.index_age))
    month_ago_date = month_ago_date.replace(tzinfo=None)
    for index in indices:
        if 'events' in index:
            index_date = index.rsplit('-', 1)[1]
            logger.debug("Checking to see if Index: %s can be closed." % (index))
            if len(index_date) == 8:
                index_date_obj = datetime.strptime(index_date, '%Y%m%d')
                try:
                    if month_ago_date > index_date_obj:
                        logger.debug("Index: %s will be closed." % (index))
                        es.close_index(index)
                    else:
                        logger.debug("Index: %s  does not meet aging criteria and will not be closed." % (index))
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
        15,
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
