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
import logging
from datetime import datetime, date, timedelta
from configlib import getConfig, OptionParser
from logging.handlers import SysLogHandler

from mozdef_util.utilities.toUTC import toUTC
from mozdef_util.elasticsearch_client import ElasticsearchClient


logger = logging.getLogger(sys.argv[0])
logger.level=logging.WARNING
formatter = logging.Formatter('%(asctime)s %(name)s %(levelname)s %(message)s')


def esCloseIndices():
    if options.output == 'syslog':
        logger.addHandler(SysLogHandler(address=(options.sysloghostname, options.syslogport)))
    else:
        sh = logging.StreamHandler(sys.stderr)
        sh.setFormatter(formatter)
        logger.addHandler(sh)
    index_to_close = ''
    logger.debug('started')
    try:
        es = ElasticsearchClient((list('{0}'.format(s) for s in options.esservers)))

        indices = es.get_indices()
        print(indices)
        # calc dates for use in index names events-YYYYMMDD, alerts-YYYYMM, etc.
        odate_month = date.strftime(toUTC(datetime.now()) - timedelta(days=int(options.index_age)), '%Y%m')
        # examine each index in the .conf file
        # for rotation settings
        for index in indices:
            if index.find('events') == -1:
                print "Index: %s will not be closed." % (index)
            else:
                odate = str(odate_month)
                if index.find(odate) == -1:
                    print "Index: %s doesn't meet aging requirements and will not be closed" % (index)
                else:
                    index_to_close = index
                    print "Index: %s will be closed." % (index_to_close)
                    es.index_close(index_to_close)
                    options.index_age = int(options.index_age) + 1
    except Exception as e:
        logger.error("Unhandled exception while closing %s, terminating: %r" % (index_to_close, e))


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
