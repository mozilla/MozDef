#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# Copyright (c) 2014 Mozilla Corporation


from lib.alerttask import AlertTask
from mozdef_util.query_models import QueryStringMatch, SearchQuery, TermMatch


class AlertProxyDropExecutable(AlertTask):
    def main(self):
        self.parse_config("proxy_drop_executable.conf", ["extensions"])

        search_query = SearchQuery(minutes=20)

        search_query.add_must(
            [
                TermMatch("category", "proxy"),
                TermMatch("details.proxyaction", "TCP_DENIED"),
            ]
        )

        # Only notify on certain file extensions from config
        filename_regex = r"/.*\.({0})/".format(self.config.extensions.replace(",", "|"))
        search_query.add_must(
            [QueryStringMatch("details.destination: {}".format(filename_regex))]
        )

        self.filtersManual(search_query)

        # Search aggregations on field 'hostname', keep X samples of
        # events at most
        self.searchEventsAggregated("details.sourceipaddress", samplesLimit=10)
        # alert when >= X matching events in an aggregation
        # I think it makes sense to alert every time here
        self.walkAggregations(threshold=1)

    # Set alert properties
    def onAggregation(self, aggreg):
        category = "squid"
        tags = ["squid", "proxy"]
        severity = "WARNING"

        dropped_urls = set()
        for event in aggreg["allevents"]:
            dropped_urls.add(event["_source"]["details"]["destination"])

        summary = "Suspicious Proxy DROP event(s) detected from {0} to the following executable file destination(s): {1}".format(
            aggreg["value"], ",".join(sorted(dropped_urls))
        )

        # Create the alert object based on these properties
        return self.createAlertDict(summary, category, tags, aggreg["events"], severity)
