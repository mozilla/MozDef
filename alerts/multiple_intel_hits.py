#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# Copyright (c) 2014 Mozilla Corporation

from lib.alerttask import AlertTask
from mozdef_util.query_models import SearchQuery, TermMatch, ExistsMatch, TermsMatch


class AlertMultipleIntelHits(AlertTask):
    def main(self):
        search_query = SearchQuery(minutes=2)

        search_query.add_must([
            TermMatch('category', 'bro'),
            TermMatch('source', 'intel'),
            ExistsMatch('details.seenindicator'),
            TermsMatch('hostname', ['sensor1', 'sensor2', 'sensor3'])
        ])

        self.filtersManual(search_query)

        # Search aggregations on field 'seenindicator', keep X samples of events at most
        self.searchEventsAggregated('details.seenindicator', samplesLimit=10)
        # alert when >= X matching events in an aggregation
        self.walkAggregations(threshold=10)

    # Set alert properties
    def onAggregation(self, aggreg):
        # aggreg['count']: number of items in the aggregation, ex: number of failed login attempts
        # aggreg['value']: value of the aggregation field, ex: toto@example.com
        # aggreg['events']: list of events in the aggregation
        category = 'bro'
        tags = ['nsm,bro,intel']
        severity = 'NOTICE'
        hostname = aggreg['events'][0]['_source']['hostname']

        summary = '{0} {1} {2} on {3}'.format(aggreg['count'], hostname, ' Bro intel match for indicator:', aggreg['value'])

        summary += ' sample hosts that hit it: '
        for e in aggreg['events'][:3]:
            if 'details' in e['_source'] \
               and 'sourceipaddress' in e['_source']['details'] \
               and 'seenwhere' in e['_source']['details']:
                interestingaddres = ''
                # someone talking to a bad guy, I want to know who
                # someone resolving bad guy's domain name, I want to know who
                # bad guy talking to someone, I want to know to whom
                if ('Conn::IN_RESP' in e['_source']['details']['seenwhere'] or
                        'HTTP::IN_HOST_HEADER' in e['_source']['details']['seenwhere'] or
                        'DNS::IN_REQUEST' in e['_source']['details']['seenwhere']):
                    interestingaddres = e['_source']['details']['sourceipaddress']
                elif ('Conn::IN_ORIG' in e['_source']['details']['seenwhere'] or
                        'HTTP::IN_X_CLUSTER_CLIENT_IP_HEADER' in e['_source']['details']['seenwhere'] or
                        'HTTP::IN_X_FORWARDED_FOR_HEADER' in e['_source']['details']['seenwhere']):
                    interestingaddres = e['_source']['details']['destinationipaddress']

                summary += '{0} in {1} '.format(interestingaddres, e['_source']['details']['seenwhere'])

        # Create the alert object based on these properties
        return self.createAlertDict(summary, category, tags, aggreg['events'], severity)
