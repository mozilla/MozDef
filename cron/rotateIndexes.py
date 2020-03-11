#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# Copyright (c) 2014 Mozilla Corporation

# set this to run as a cronjob at 00:00 UTC to create the indexes
# necessary for mozdef
# .conf file will determine what indexes are operated on
# Create a starter .conf file with backupDiscover.py

import sys
from datetime import datetime
from datetime import date
from datetime import timedelta
from configlib import getConfig, OptionParser
import json

import os
from mozdef_util.utilities.toUTC import toUTC
from mozdef_util.utilities.logger import logger
from mozdef_util.elasticsearch_client import ElasticsearchClient


def daterange(start_date, end_date):
    for n in range((end_date - start_date).days + 1):
        yield start_date + timedelta(n)


def esRotateIndexes():
    logger.debug('started')
    with open(options.default_mapping_file, 'r') as mapping_file:
        default_mapping_contents = json.loads(mapping_file.read())

    try:
        es = ElasticsearchClient((list('{0}'.format(s) for s in options.esservers)))

        indices = es.get_indices()

        # calc dates for use in index names events-YYYYMMDD, alerts-YYYYMM, etc.
        odate_day = date.strftime(toUTC(datetime.now()) - timedelta(days=1), '%Y%m%d')
        odate_month = date.strftime(toUTC(datetime.now()) - timedelta(days=1), '%Y%m')
        ndate_day = date.strftime(toUTC(datetime.now()), '%Y%m%d')
        ndate_month = date.strftime(toUTC(datetime.now()), '%Y%m')
        # examine each index in the .conf file
        # for rotation settings
        for (index, dobackup, rotation, pruning) in zip(options.indices, options.dobackup, options.rotation, options.pruning):
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
                        index_settings = {}
                        if 'events' in newindex:
                            index_settings = {
                                "index": {
                                    "refresh_interval": options.refresh_interval,
                                    "number_of_shards": options.number_of_shards,
                                    "number_of_replicas": options.number_of_replicas,
                                    "search.slowlog.threshold.query.warn": options.slowlog_threshold_query_warn,
                                    "search.slowlog.threshold.fetch.warn": options.slowlog_threshold_fetch_warn,
                                    "mapping.total_fields.limit": options.mapping_total_fields_limit
                                }
                            }
                        elif 'alerts' in newindex:
                            index_settings = {
                                "index": {
                                    "number_of_shards": 1
                                }
                            }
                        default_mapping_contents['settings'] = index_settings
                        logger.debug('Creating %s index' % newindex)
                        es.create_index(newindex, default_mapping_contents)
                    # set aliases: events to events-YYYYMMDD
                    # and events-previous to events-YYYYMMDD-1
                    logger.debug('Setting {0} alias to index: {1}'.format(index, newindex))
                    es.create_alias(index, newindex)
                    if oldindex in indices:
                        logger.debug('Setting {0}-previous alias to index: {1}'.format(index, oldindex))
                        es.create_alias('%s-previous' % index, oldindex)
                    else:
                        logger.debug('Old index %s is missing, do not change %s-previous alias' % (oldindex, index))
            except Exception as e:
                logger.error("Unhandled exception while rotating %s, terminating: %r" % (index, e))

        indices = es.get_indices()
        # Create weekly aliases for certain indices
        week_ago_date = toUTC(datetime.now()) - timedelta(weeks=1)
        week_ago_str = week_ago_date.strftime('%Y%m%d')
        current_date = toUTC(datetime.now())
        for index in options.weekly_rotation_indices:
            weekly_index_alias = '%s-weekly' % index
            logger.debug('Trying to re-alias {0} to indices since {1}'.format(weekly_index_alias, week_ago_str))
            existing_weekly_indices = []
            for day_obj in daterange(week_ago_date, current_date):
                day_str = day_obj.strftime('%Y%m%d')
                day_index = index + '-' + str(day_str)
                if day_index in indices:
                    existing_weekly_indices.append(day_index)
                else:
                    logger.debug('%s not found, so cant assign weekly alias' % day_index)
            if existing_weekly_indices:
                logger.debug('Creating {0} alias for {1}'.format(weekly_index_alias, existing_weekly_indices))
                es.create_alias_multiple_indices(weekly_index_alias, existing_weekly_indices)
            else:
                logger.warning('No indices within the past week to assign events-weekly to')
    except Exception as e:
        logger.error("Unhandled exception, terminating: %r" % e)


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
        'events,alerts,.kibana',
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
    options.weekly_rotation_indices = list(getConfig(
        'weekly_rotation_indices',
        'events',
        options.configfile).split(',')
    )

    default_mapping_location = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'defaultMappingTemplate.json')
    options.default_mapping_file = getConfig('default_mapping_file', default_mapping_location, options.configfile)
    options.refresh_interval = getConfig('refresh_interval', '1s', options.configfile)
    options.number_of_shards = getConfig('number_of_shards', '1', options.configfile)
    options.number_of_replicas = getConfig('number_of_replicas', '1', options.configfile)
    options.slowlog_threshold_query_warn = getConfig('slowlog_threshold_query_warn', '5s', options.configfile)
    options.slowlog_threshold_fetch_warn = getConfig('slowlog_threshold_fetch_warn', '5s', options.configfile)
    options.mapping_total_fields_limit = getConfig('mapping_total_fields_limit', '1000', options.configfile)


if __name__ == '__main__':
    parser = OptionParser()
    parser.add_option("-c",
                      dest='configfile',
                      default=sys.argv[0].replace('.py', '.conf'),
                      help="configuration file to use")
    (options, args) = parser.parse_args()
    initConfig()
    esRotateIndexes()
