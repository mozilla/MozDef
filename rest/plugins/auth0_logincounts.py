# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
# Copyright (c) 2014 Mozilla Corporation

import requests
import json
import os
import sys
from configlib import getConfig, OptionParser
from datetime import datetime, timedelta
from mozdef_util.elasticsearch_client import ElasticsearchClient, ElasticsearchInvalidIndex
from mozdef_util.query_models import SearchQuery, TermMatch, TermsMatch, QueryStringMatch, RangeMatch, Aggregation, ExistsMatch
from mozdef_util.utilities.toUTC import toUTC
from mozdef_util.utilities.logger import logger, initLogger


class message(object):
    def __init__(self):
        '''register our criteria for being passed a message
           as a list of lower case strings to match with an rest endpoint
           (i.e. blockip matches /blockip)
           set the priority if you have a preference for order of plugins
           0 goes first, 100 is assumed/default if not sent

           Plugins will register in Meteor with attributes:
           name: (as below)
           description: (as below)
           priority: (as below)
           file: "plugins.filename" where filename.py is the plugin code.

           Plugin gets sent main rest options as:
           self.restoptions
           self.restoptions['configfile'] will be the .conf file
           used by the restapi's index.py file.

        '''

        self.registration = ['logincounts']
        self.priority = 5
        self.name = "auth0LoginCounts"
        self.description = "count failures/success logins"

        # set my own conf file
        # relative path to the rest index.py file
        self.configfile = './plugins/auth0_logincounts.conf'
        self.options = None
        if os.path.exists(self.configfile):
            sys.stdout.write('found conf file {0}\n'.format(self.configfile))
            self.initConfiguration()

    def onMessage(self, request, response):
        '''
        request: http://bottlepy.org/docs/dev/api.html#the-request-object
        response: http://bottlepy.org/docs/dev/api.html#the-response-object

        '''
        # an ES query/facet to count success/failed logins
        # oriented to the data sent via auth02mozdef.py
        begindateUTC=None
        enddateUTC=None
        resultsList = list()
        if begindateUTC is None:
            begindateUTC = datetime.now() - timedelta(hours=12)
            begindateUTC = toUTC(begindateUTC)
        if enddateUTC is None:
            enddateUTC = datetime.now()
            enddateUTC = toUTC(enddateUTC)

        es_client = ElasticsearchClient(list('{0}'.format(s) for s in self.restoptions['esservers']))
        search_query = SearchQuery()
        # a query to tally users with failed logins
        date_range_match = RangeMatch('utctimestamp', begindateUTC, enddateUTC)
        search_query.add_must(date_range_match)
        search_query.add_must(TermMatch('tags', 'auth0'))
        search_query.add_must(QueryStringMatch('failed'))
        search_query.add_must(ExistsMatch('details.username'))
        search_query.add_aggregation(Aggregation('details.type'))
        search_query.add_aggregation(Aggregation('details.username'))

        results = search_query.execute(es_client, indices=['events','events-previous'])

        # any usernames or words to ignore
        # especially useful if ES is analyzing the username field and breaking apart user@somewhere.com
        # into user somewhere and .com
        stoplist =['']
        # walk the aggregate failed users
        # and look for successes/failures
        for t in results['aggregations']['details.username']['terms']:
            if t['key'] in stoplist:
                continue
            failures = 0
            success = 0
            username = t['key']

            details_query = SearchQuery()
            details_query.add_must(date_range_match)
            details_query.add_must(TermMatch('tags', 'auth0'))
            details_query.add_must(TermMatch('details.username', username))
            details_query.add_aggregation(Aggregation('details.type'))

            results = details_query.execute(es_client)
            # details.type is usually "Success Login" or "Failed Login"
            for t in results['aggregations']['details.type']['terms']:
                if 'success' in t['key'].lower():
                    success = t['count']
                if 'fail' in t['key'].lower():
                    failures = t['count']
            resultsList.append(
                dict(
                    username=username,
                    failures=failures,
                    success=success,
                    begin=begindateUTC.isoformat(),
                    end=enddateUTC.isoformat()
                )
            )

        response.body = json.dumps(resultsList)
        response.status = 200

        return (request, response)

    def initConfiguration(self):
        myparser = OptionParser()
        # setup self.options by sending empty list [] to parse_args
        (self.options, args) = myparser.parse_args([])

        # fill self.options with plugin-specific options

        # options
        self.options.ignoreusernames = getConfig('ignoreusernames',
                                                 '',
                                                 self.configfile)
