#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
# Copyright (c) 2014 Mozilla Corporation
#
# Contributors:
# Jeff Bryner jbryner@mozilla.com
# Anthony Verez averez@mozilla.com

# set this to run as a cronjob (after backup has completed)
# to regularly remove indexes

# .conf file will determine what indexes are operated on
# Create a starter .conf file with backupDiscover.py

import sys
import pyes
import logging
from datetime import datetime
from datetime import date
from datetime import timedelta
from configlib import getConfig, OptionParser


logger = logging.getLogger(sys.argv[0])
logger.level=logging.INFO
formatter = logging.Formatter('%(asctime)s %(name)s %(levelname)s %(message)s')


def esPruneIndexes():
    if options.output == 'syslog':
        logger.addHandler(SysLogHandler(address=(options.sysloghostname, options.syslogport)))
    else:
        sh = logging.StreamHandler(sys.stderr)
        sh.setFormatter(formatter)
        logger.addHandler(sh)

    logger.debug('started')
    try:
        es = pyes.ES((list('{0}'.format(s) for s in options.esservers)))
        indices = es.indices.stats()['indices'].keys()
        # do the pruning
        for (index, dobackup, rotation, pruning) in zip(options.indices,
            options.dobackup, options.rotation, options.pruning):
            try:
                if pruning != '0':
                    index_to_prune = index
                    if rotation == 'daily':
                        idate = date.strftime(datetime.utcnow()-timedelta(days=int(pruning)),'%Y%m%d')
                        index_to_prune += '-%s' % idate
                    elif rotation == 'monthly':
                        idate = date.strftime(datetime.utcnow()-timedelta(days=31*int(pruning)),'%Y%m')
                        index_to_prune += '-%s' % idate

                    if index_to_prune in indices:
                        logger.info('Deleting index: %s' % index_to_prune)
                        es.indices.delete_index(index_to_prune)
                    else:
                        logger.error('Error deleting index %s, index missing' % index_to_prune)
            except Exception as e:
                logger.error("Unhandled exception while deleting %s, terminating: %r" % (index_to_prune, e))

    except Exception as e:
        logger.error("Unhandled exception, terminating: %r"%e)


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
    options.indices = list(getConfig(
        'backup_indices',
        'events,alerts,kibana-int',
        options.configfile).split(',')
        )
    options.dobackup = list(getConfig(
        'backup_dobackup',
        '1,1,1',
        options.configfile).split(',')
        )
    options.rotation = list(getConfig(
        'backup_rotation',
        'daily,monthly,none',
        options.configfile).split(',')
        )
    options.pruning = list(getConfig(
        'backup_pruning',
        '20,0,0',
        options.configfile).split(',')
        )

if __name__ == '__main__':
    parser = OptionParser()
    parser.add_option("-c",
                      dest='configfile',
                      default=sys.argv[0].replace('.py', '.conf'),
                      help="configuration file to use")
    (options, args) = parser.parse_args()
    initConfig()
    esPruneIndexes()
