#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
# Copyright (c) 2014 Mozilla Corporation
#
# Contributors:
# Jeff Bryner jbryner@mozilla.com
# Anthony Verez averez@mozilla.com

# set this to run as a cronjob at 00:00 UTC to create the indexes
# necessary for mozdef
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
logger.level=logging.DEBUG
formatter = logging.Formatter('%(asctime)s %(name)s %(levelname)s %(message)s')


def esRotateIndexes():
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
        # calc dates for use in index names events-YYYYMMDD, alerts-YYYYMM, etc.
        odate_day = date.strftime(datetime.utcnow()-timedelta(days=1),'%Y%m%d')
        odate_month = date.strftime(datetime.utcnow()-timedelta(days=1),'%Y%m')
        ndate_day = date.strftime(datetime.utcnow(),'%Y%m%d')
        ndate_month = date.strftime(datetime.utcnow(),'%Y%m')
        
        # examine each index in the .conf file
        # for rotation settings
        for (index, dobackup, rotation, pruning) in zip(options.indices,
            options.dobackup, options.rotation, options.pruning):
            try:
                if rotation != 'none':
                    oldindex = index
                    newindex = index
                    if rotation == 'daily':
                        oldindex += '-%s' % odate_day
                        newindex += '-%s' % ndate_day
                    elif rotation == 'monthly':
                        oldindex += '-%s' % odate_month
                        newindex += '-%s' % ndate_month
                        # do not rotate before the month ends
                        if oldindex == newindex:
                            logger.debug('do not rotate %s index, month has not changed yet' % index)
                            continue
                    if newindex not in indices:
                        logger.debug('Creating %s index' % newindex)
                        es.indices.create_index(newindex)
                    # set aliases: events to events-YYYYMMDD
                    # and events-previous to events-YYYYMMDD-1 for example
                    logger.debug('Setting {0} alias to index: {1}'.format(index, newindex))
                    es.indices.set_alias(index, newindex)
                    if oldindex in indices:
                        logger.debug('Setting {0}-previous alias to index: {1}'.format(index, oldindex))
                        es.indices.set_alias('%s-previous' % index, oldindex)
                    else:
                        logger.debug('Old index %s is missing, do not change %s-previous alias' % (oldindex, index))
            except Exception as e:
                logger.error("Unhandled exception while rotating %s, terminating: %r" % (index, e))

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
    esRotateIndexes()
