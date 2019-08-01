# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# Copyright (c) 2014 Mozilla Corporation

import json
import os
from configlib import getConfig, OptionParser
from datetime import datetime, timedelta
from mozdef_util.elasticsearch_client import ElasticsearchClient
from mozdef_util.query_models import SearchQuery, RangeMatch, Aggregation, ExistsMatch, PhraseMatch
from mozdef_util.utilities.toUTC import toUTC
from mozdef_util.utilities.logger import logger


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
        self.name = "loginCounts"
        self.description = "count failures/success logins"

        # set my own conf file
        # relative path to the rest index.py file
        self.configfile = './plugins/logincounts.conf'
        self.options = None
        if os.path.exists(self.configfile):
            logger.debug('found conf file {0}\n'.format(self.configfile))
        self.initConfiguration()

    def onMessage(self, request, response):
        '''
        request: http://bottlepy.org/docs/dev/api.html#the-request-object
        response: http://bottlepy.org/docs/dev/api.html#the-response-object

        '''
        # an ES query/facet to count success/failed logins
        # oriented to the data having
        # category: authentication
        # details.success marked true/false for success/failed auth
        # details.username as the user

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
        search_query.add_must(PhraseMatch('category', 'authentication'))
        search_query.add_must(PhraseMatch('details.success','false'))
        search_query.add_must(ExistsMatch('details.username'))
        search_query.add_aggregation(Aggregation('details.success'))
        search_query.add_aggregation(Aggregation('details.username'))

        results = search_query.execute(es_client, indices=['events','events-previous'])

        # any usernames or words to ignore
        # especially useful if ES is analyzing the username field and breaking apart user@somewhere.com
        # into user somewhere and .com
        stoplist =self.options.ignoreusernames.split(',')
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
            details_query.add_must(PhraseMatch('category', 'authentication'))
            details_query.add_must(PhraseMatch('details.username', username))
            details_query.add_aggregation(Aggregation('details.success'))

            details_results = details_query.execute(es_client)
            # details.success is boolean. As an aggregate is an int (0/1)
            for details_term in details_results['aggregations']['details.success']['terms']:
                if details_term['key'] == 1:
                    success = details_term['count']
                if details_term['key'] == 0:
                    failures = details_term['count']
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
        # comma separated list of usernames to exclude
        # from the data
        self.options.ignoreusernames = getConfig('ignoreusernames',
                                                 '',
                                                 self.configfile)
