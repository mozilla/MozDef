#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
# Copyright (c) 2014 Mozilla Corporation


from lib.alerttask import AlertTask
from query_models import QueryStringMatch, SearchQuery, TermMatch, ExistsMatch


class AlertProxyDropExecutable(AlertTask):
    def main(self):

        superquery = None
        run = 0

        self.parse_config('proxy_drop_executable.conf', [
                          'destinationfilter', 'extensions'])

        search_query = SearchQuery(minutes=5)

        search_query.add_must([
            TermMatch('category', 'squid'),
            TermMatch('tags', 'squid'),
            TermMatch('details.proxyaction', 'TCP_DENIED/-')
        ])

        search_query.add_must_not([
            QueryStringMatch(
                'details.destination: /{}/'.format(self.config.destinationfilter)),
        ])

        # TODO: remove HACK in onAggregation once this works as expected
        # for extension in self.config.extensions.split(','):
        #     if run == 0:
        #         superquery = QueryStringMatch(
        #             'details.destination: /{0}/'.format(extension))
        #     else:
        #         superquery |= QueryStringMatch(
        #             'details.destination: /{0}/'.format(extension))
        #     run += 1
        #
        # search_query.add_must(superquery)

        self.filtersManual(search_query)

        # Search aggregations on field 'hostname', keep X samples of
        # events at most
        self.searchEventsAggregated('details.sourceipaddress', samplesLimit=10)
        # alert when >= X matching events in an aggregation
        # I think it makes sense to alert every time here
        self.walkAggregations(threshold=1)

    # Set alert properties
    def onAggregation(self, aggreg):
        # aggreg['count']: number of items in the aggregation, ex: number of failed login attempts
        # aggreg['value']: value of the aggregation field, ex: toto@example.com
        # aggreg['events']: list of events in the aggregation
        category = 'squid'
        tags = ['squid', 'proxy']
        severity = 'WARNING'

        dropped_url_destinations = []

        # START HACK - The conditionals here are to account for an inability to endwith
        # in lucene search, which we are hacking in as python
        for event in aggreg['allevents']:
            for extension in self.config.extensions.split(','):
                if event['_source']['details']['destination'].endswith(extension):
                    dropped_url_destinations.append(
                        event['_source']['details']['destination'])

        if len(dropped_url_destinations) == 0:
            return
        # END HACK

        summary = 'Multiple Proxy DROP events detected from {0} to the following executable file destination(s): {1}'.format(
            aggreg['value'], ",".join(sorted(set(dropped_url_destinations))))

        # Create the alert object based on these properties
        return self.createAlertDict(summary, category, tags, aggreg['events'], severity)
