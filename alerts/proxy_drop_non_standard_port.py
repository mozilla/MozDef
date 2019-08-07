#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# Copyright (c) 2014 Mozilla Corporation


from lib.alerttask import AlertTask
from mozdef_util.query_models import SearchQuery, TermMatch


class AlertProxyDropNonStandardPort(AlertTask):
    def main(self):
        self.parse_config("proxy_drop_non_standard_port.conf", ["excludedports"])

        search_query = SearchQuery(minutes=20)

        search_query.add_must(
            [
                TermMatch("category", "proxy"),
                TermMatch("details.proxyaction", "TCP_DENIED"),
                TermMatch("details.method", "CONNECT"),
            ]
        )
        for port in self.config.excludedports.split(","):
            search_query.add_must_not([TermMatch("details.destinationport", port)])

        self.filtersManual(search_query)

        # Search aggregations on field 'hostname', keep X samples of
        # events at most
        self.searchEventsAggregated("details.sourceipaddress", samplesLimit=10)
        # alert when >= X matching events in an aggregation
        # I think it makes sense to alert every time here
        self.walkAggregations(threshold=1)

    def onAggregation(self, aggreg):
        category = "squid"
        tags = ["squid", "proxy"]
        severity = "WARNING"

        destinations = set()
        for event in aggreg["allevents"]:
            destinations.add(event["_source"]["details"]["destination"])

        summary = "Suspicious Proxy DROP event(s) detected from {0} to the following non-std port destination(s): {1}".format(
            aggreg["value"], ",".join(sorted(destinations))
        )

        # Create the alert object based on these properties
        return self.createAlertDict(summary, category, tags, aggreg["events"], severity)
