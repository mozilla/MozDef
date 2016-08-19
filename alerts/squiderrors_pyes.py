#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
# Copyright (c) 2014 Mozilla Corporation
#
# Contributors:
# Guillaume Destuynder gdestuynder@mozilla.com

# Sample msg
#{
#  "_index": "events-20151022",
#  "_type": "event",
#  "_id": "Fr5Nitk4TXyvwULHF3rRrg",
#  "_score": null,
#  "_source": {
#    "category": "syslog",
#    "receivedtimestamp": "2015-10-22T18:29:40.695767+00:00",
#    "utctimestamp": "2015-10-22T18:00:47+00:00",
#    "tags": [
#      "nubis_events_non_prod"
#    ],
#    "timestamp": "2015-10-22T18:00:47+00:00",
#    "mozdefhostname": "mozdefqa1.private.scl3.mozilla.com",
#    "summary": "1445536847.673    856 10.162.14.83 TCP_MISS/200 58510 CONNECT www.mozilla.org:443 - HIER_DIRECT/63.245.215.20 -",
#    "source": "syslog",
#    "details": {
#      "__tag": "ec2.forward.squid.access",
#      "region": "us-east-1",
#      "instance_id": "i-1086c1c4",
#      "instance_type": "m3.medium",
#      "time": "2015-10-22T18:00:47Z",
#      "message": "1445536847.673    856 10.162.14.83 TCP_MISS/200 58510 CONNECT www.mozilla.org:443 - HIER_DIRECT/63.245.215.20 -",
#      "az": "us-east-1b"
#    }
#  },
#  "sort": [
#    1445536847000
#  ]

from lib.alerttask import AlertTask
from query_models import SearchQuery, TermMatch, PhraseMatch


class AlertHTTPErrors(AlertTask):
    def main(self):
        search_query = SearchQuery(minutes=15)

        search_query.add_must([
            TermMatch('tags', 'nubis_events_non_prod'),
            TermMatch('tags', 'nubis_events_prod'),
            TermMatch('category', 'syslog'),
            TermMatch('details.__tag', 'ec2.forward.squid.access'),
            PhraseMatch('details.summary', 'is DENIED, because it matched'),
        ])

        self.filtersManual(search_query)

        # Search events
        self.searchEventsSimple()
        self.walkEvents()

    # Set alert properties
    def onEvent(self, event):
        category = 'squiderrors'
        tags = ['http', 'squid', 'proxy', 'nubis_events']
        severity = 'NOTICE'
        hostname = event['_source']['hostname']
        url = "https://mana.mozilla.org/wiki/display/SECURITY/Notes%3A+Nubis+AWS"

        # the summary of the alert is the same as the event
        summary = '{0} {1}'.format(hostname, event['_source']['summary'])

        # Create the alert object based on these properties
        return self.createAlertDict(summary, category, tags, [event], severity=severity, url=url)
