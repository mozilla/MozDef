#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
# Copyright (c) 2017 Mozilla Corporation

import sys
import os
from configlib import getConfig, OptionParser

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../lib'))
from elasticsearch_client import ElasticsearchClient
from query_models import SearchQuery, ExistsMatch, Aggregation, TermMatch
from utilities.logger import logger, initLogger


def verify_events(options):
    es_client = ElasticsearchClient(options.esservers)
    for required_field in options.required_fields:
        logger.debug('Looking for events without ' + required_field)
        search_query = SearchQuery(hours=12)
        search_query.add_must_not(ExistsMatch(required_field))

        # Exclude all events that are mozdef related health and stats
        search_query.add_must_not(TermMatch('category', 'mozdefstats'))
        search_query.add_must_not(TermMatch('category', 'mozdefhealth'))

        search_query.add_aggregation(Aggregation('category'))
        # We don't care about the actual events, we only want the numbers
        results = search_query.execute(es_client, size=1)
        for aggreg_term in results['aggregations']['category']['terms']:
            count = aggreg_term['count']
            category_name = aggreg_term['key']
            logger.error("Found {0} bad events of category '{1}' missing '{2}' field".format(
                count,
                category_name,
                required_field
            ))


def main():
    logger.debug('Starting')
    logger.debug(options)
    verify_events(options)


def initConfig():
    # output our log to stdout or syslog
    options.output = getConfig('output', 'stdout', options.configfile)
    options.sysloghostname = getConfig('sysloghostname', 'localhost', options.configfile)
    options.syslogport = getConfig('syslogport', 514, options.configfile)

    options.required_fields = getConfig('required_fields', '', options.configfile).split(',')
    options.esservers = getConfig('esservers', '', options.configfile).split(',')


if __name__ == '__main__':
    parser = OptionParser()
    parser.add_option(
        "-c",
        dest='configfile',
        default=sys.argv[0].replace('.py', '.conf'),
        help="configuration file to use")
    (options, args) = parser.parse_args()
    initConfig()
    initLogger(options)
    main()
