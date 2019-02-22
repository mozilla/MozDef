#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
# Copyright (c) 2014 Mozilla Corporation


from lib.alerttask import AlertTask
from mozdef_util.query_models import QueryStringMatch, SearchQuery, TermMatch
import re


class AlertProxyDropIP(AlertTask):
    def main(self):
        search_query = SearchQuery(minutes=20)

        search_query.add_must(
            [
                TermMatch("category", "proxy"),
                TermMatch("details.proxyaction", "TCP_DENIED"),
            ]
        )

        # Match on 1.1.1.1, http://1.1.1.1, or https://1.1.1.1
        # This will over-match on short 3-char domains like foo.bar.baz.com, but will get weeded out below
        ip_regex = "/.*\..{1,3}\..{1,3}\..{1,3}(:.*|\/.*)/"
        search_query.add_must(
            [QueryStringMatch("details.destination: {}".format(ip_regex))]
        )
        https: // www.programcreek.com / python / example / 57082 / netaddr.IPNetwork
        >>> ip = ipaddr.IPAddress("onet.pl")
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
  File "/Users/michalpurzynski/.pyenv/versions/mozdef/lib/python2.7/site-packages/ipaddr.py", line 78, in IPAddress
    address)
ValueError: 'onet.pl' does not appear to be an IPv4 or IPv6 address

        self.filtersManual(search_query)
        self.searchEventsAggregated("details.sourceipaddress", samplesLimit=10)
        self.walkAggregations(threshold=1)

    # Set alert properties
    def onAggregation(self, aggreg):
        category = "squid"
        tags = ["squid", "proxy"]
        severity = "WARNING"

        # Lucene search has a slight potential for overmatches, so we'd double-check
        # with this pattern to ensure it's truely an IP before we add dest to our dropped list
        pattern = r"^(http:\/\/|https:\/\/|)\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}"

        dropped_destinations = set()

        for event in aggreg["allevents"]:
            if re.search(pattern, event["_source"]["details"]["destination"]):
                dropped_destinations.add(event["_source"]["details"]["destination"])

        # If it's all over-matches, don't throw the alert
        if len(dropped_destinations) == 0:
            return None

        summary = "Suspicious Proxy DROP event(s) detected from {0} to the following IP-based destination(s): {1}".format(
            aggreg["value"], ",".join(sorted(dropped_destinations))
        )

        return self.createAlertDict(summary, category, tags, aggreg["events"], severity)
