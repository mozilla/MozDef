#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# Copyright (c) 2017 Mozilla Corporation

import sys
from configlib import getConfig, OptionParser

from mozdef_util.elasticsearch_client import ElasticsearchClient
from mozdef_util.query_models import SearchQuery, ExistsMatch, Aggregation, TermMatch
from mozdef_util.utilities.logger import logger, initLogger


def verify_events(options):
    es_client = ElasticsearchClient(options.esservers)
    for required_field in options.required_fields:
        logger.debug('Looking for events without ' + required_field)
        search_query = SearchQuery(hours=12)
        search_query.add_must_not(ExistsMatch(required_field))

        # Exclude all events that are mozdef related health and stats
        search_query.add_must_not(TermMatch('type', 'mozdefstats'))
        search_query.add_must_not(TermMatch('type', 'mozdefhealth'))

        search_query.add_aggregation(Aggregation('type'))
        # We don't care about the actual events, we only want the numbers
        results = search_query.execute(es_client, size=1)
        for aggreg_term in results['aggregations']['type']['terms']:
            count = aggreg_term['count']
            category = aggreg_term['key']
            logger.error("Found {0} bad events of type '{1}' missing '{2}' field".format(
                count,
                category,
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
