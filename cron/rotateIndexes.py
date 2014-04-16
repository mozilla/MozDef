#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
# Copyright (c) 2014 Mozilla Corporation
#
# Contributors:
# Jeff Bryner jbryner@mozilla.com

# set this to run as a cronjob at 00:00 UTC to create the indexes
# necessary for mozdef

import sys
import pyes
from datetime import datetime
from datetime import date
from datetime import timedelta
from configlib import getConfig, OptionParser


def esRotateIndexes():
    es = pyes.ES((list('{0}'.format(s) for s in options.esservers)))

    indexes = es.indices.stats()['indices'].keys()
    # print('[*]\tcurrent indexes: {0}'.format(indexes))

    # set index names events-YYYYMMDD, alerts-YYYYMM, etc.
    dtNow = datetime.utcnow()
    indexSuffix = date.strftime(dtNow, '%Y%m%d')
    # rotate daily
    eventsIndexName = 'events-{0}'.format(indexSuffix)
    # rotate monthly
    indexSuffix = date.strftime(dtNow, '%Y%m')
    alertsIndexName = 'alerts-{0}'.format(indexSuffix)
    correlationsIndexName = 'correlations-{0}'.format(indexSuffix)
    print('[*]\tlooking for current daily indexes: {0},{1},{2}'.format(
        eventsIndexName,
        alertsIndexName,
        correlationsIndexName))

    if eventsIndexName not in indexes:
        print('[*]\tcreating: {0}'.format(eventsIndexName))
        es.indices.create_index(eventsIndexName)
    if alertsIndexName not in indexes:
        print('[*]\tcreating: {0}'.format(alertsIndexName))
        es.indices.create_index(alertsIndexName)
    # not yet
    # if correlationsIndexName not in indexes:
        # print('[*]\tcreating: {0}'.format(correlationsIndexName))
        # es.indices.create_index(correlationsIndexName)

    print('[*]\tensuring aliases are current')
    es.indices.set_alias('events', eventsIndexName)
    es.indices.set_alias('alerts', alertsIndexName)
    # es.indices.set_alias('correlations', correlationsIndexName)

    # set an alias for yesterday's events to make it easier
    # to limit queries by indexes
    # for alert/correlation searches.
    previousSuffix = date.strftime(dtNow - timedelta(days=1), '%Y%m%d')
    eventsPrevious = 'events-{0}'.format(previousSuffix)
    if eventsPrevious in indexes:
        es.indices.set_alias('events-previous', eventsPrevious)
    else:
        # we must be brand new, set previous alias to the same as now
        es.indices.set_alias('events-previous', eventsIndexName)


def initConfig():
    options.esservers = list(getConfig(
        'esservers',
        'http://localhost:9200',
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
