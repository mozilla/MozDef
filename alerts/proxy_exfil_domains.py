#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# Copyright (c) 2014 Mozilla Corporation


from lib.alerttask import AlertTask
from mozdef_util.query_models import SearchQuery, TermMatch


class AlertProxyExfilDomains(AlertTask):
    def main(self):
        self.parse_config("proxy_exfil_domains.conf", ["exfil_domains"])

        search_query = SearchQuery(minutes=20)

        search_query.add_must([TermMatch("category", "proxy")])

        for domain in self.config.exfil_domains.split(","):
            search_query.add_should([TermMatch("details.host", domain)])

        self.filtersManual(search_query)

        # Search aggregations on field 'hostname', keep X samples of
        # events at most
        self.searchEventsAggregated("details.sourceipaddress", samplesLimit=10)
        # alert when >= X matching events in an aggregation
        # I think it makes sense to alert every time here
        self.walkAggregations(threshold=1)

    # Set alert properties
    def onAggregation(self, aggreg):
        # aggreg['count']: number of items in the aggregation, ex: number of failed login attempts
        # aggreg['value']: value of the aggregation field, ex: toto@example.com
        # aggreg['events']: list of events in the aggregation
        category = "squid"
        tags = ["squid", "proxy"]
        severity = "WARNING"

        exfil_domains = set()
        for event in aggreg["allevents"]:
            domain = event["_source"]["details"]["host"]
            exfil_domains.add(domain)

        summary = "Proxy drop events detected from {0} to the following domain(s) that are known for exfiltrating data: {1}".format(
            aggreg["value"], ",".join(sorted(exfil_domains))
        )

        # Create the alert object based on these properties
        return self.createAlertDict(summary, category, tags, aggreg["events"], severity)
