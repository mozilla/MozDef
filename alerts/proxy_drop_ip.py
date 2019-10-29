#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# Copyright (c) 2014 Mozilla Corporation


from lib.alerttask import AlertTask
from mozdef_util.query_models import QueryStringMatch, SearchQuery, TermMatch
import netaddr


class AlertProxyDropIP(AlertTask):
    def main(self):
        self.parse_config("proxy_drop_ip.conf", ["ip_whitelist"])

        search_query = SearchQuery(minutes=20)

        search_query.add_must(
            [
                TermMatch("category", "proxy"),
                TermMatch("details.proxyaction", "TCP_DENIED"),
            ]
        )

        # Match on everything that looks like the first octet of either the IPv4 or the IPv6 address
        # This will over-match, but will get weeded out below
        ip_regex = "/[0-9a-fA-F]{1,4}.*/"

        search_query.add_must([QueryStringMatch("details.host: {}".format(ip_regex))])

        for ip in self.config.ip_whitelist.split(","):
            search_query.add_must_not([TermMatch("details.host", ip)])

        self.filtersManual(search_query)
        self.searchEventsAggregated("details.sourceipaddress", samplesLimit=10)
        self.walkAggregations(threshold=1)

    # Set alert properties
    def onAggregation(self, aggreg):
        category = "squid"
        tags = ["squid", "proxy"]
        severity = "WARNING"

        dropped_destinations = set()
        final_aggr = {}
        final_aggr["value"] = aggreg["value"]
        final_aggr["allevents"] = []
        final_aggr["events"] = []

        i = 0
        for event in aggreg["allevents"]:
            ip = None
            try:
                ip = netaddr.IPAddress(event["_source"]["details"]["host"])
            except (netaddr.core.AddrFormatError, ValueError):
                pass
            if ip is not None:
                dropped_destinations.add(event["_source"]["details"]["host"])
                final_aggr["allevents"].append(event)
                final_aggr["events"].append(event)
                i += i
        final_aggr["count"] = i

        # If it's all over-matches, don't throw the alert
        if len(dropped_destinations) == 0:
            return None

        summary = "Suspicious Proxy DROP event(s) detected from {0} to the following IP-based destination(s): {1}".format(
            final_aggr["value"], ",".join(sorted(dropped_destinations))
        )

        return self.createAlertDict(
            summary, category, tags, final_aggr["allevents"], severity
        )
