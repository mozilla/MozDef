#!/usr/bin/env python
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# set this to run as a cronjob 
# to reguarly remove indexes 
# run it after backup of course

import sys
import pyes
from datetime import datetime
from datetime import date
from datetime import timedelta
from configlib import getConfig, OptionParser


def esPruneIndexes():
    es = pyes.ES((list('{0}'.format(s) for s in options.esservers)))

    indexes = es.indices.stats()['indices'].keys()
    # print('[*]\tcurrent indexes: {0}'.format(indexes))

    # set index names events-YYYYMMDD, alerts-YYYYMM, etc.
    dtNow = datetime.utcnow()
    targetSuffix=date.strftime(dtNow- timedelta(days=options.days),'%Y%m%d')
    
    # rotate daily
    eventsIndexName = 'events-{0}'.format(targetSuffix)
    
    # rotate monthly
    targetSuffix = date.strftime(dtNow- timedelta(days=options.months*30), '%Y%m')
    alertsIndexName = 'alerts-{0}'.format(targetSuffix)
    correlationsIndexName = 'correlations-{0}'.format(targetSuffix)
      
    print('[*]\tlooking for old indexes: {0},{1},{2}'.format(
        eventsIndexName,
        alertsIndexName,
        correlationsIndexName))

    if eventsIndexName in indexes:
        print('[*]\tdeleting: {0}'.format(eventsIndexName))
        es.indices.delete_index(eventsIndexName)
    if alertsIndexName in indexes:
        print('[*]\tdeleting: {0}'.format(alertsIndexName))
        es.indices.delete_index(alertsIndexName)
    if correlationsIndexName in indexes:
        print('[*]\tdeleting: {0}'.format(correlationsIndexName))
        es.indices.delete_index(correlationsIndexName)

def initConfig():
    options.esservers = list(getConfig(
        'esservers',
        'http://localhost:9200',
        options.configfile).split(',')
        )
    # how many days of events to retain for daily rotations
    options.days = getConfig('days', 20, options.configfile)
    # how many months of events to retain for monthly rotations
    options.months = getConfig('months', 3, options.configfile)

if __name__ == '__main__':
    parser = OptionParser()
    parser.add_option("-c",
                      dest='configfile',
                      default=sys.argv[0].replace('.py', '.conf'),
                      help="configuration file to use")
    (options, args) = parser.parse_args()
    initConfig()
    esPruneIndexes()
