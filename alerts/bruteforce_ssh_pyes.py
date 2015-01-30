#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
# Copyright (c) 2014 Mozilla Corporation
#
# Contributors:
# Anthony Verez averez@mozilla.com
# Jeff Bryner jbryner@mozilla.com

from lib.alerttask import AlertTask
import pyes

class AlertBruteforceSsh(AlertTask):
    def main(self):
        # look for events in last 15 mins
        date_timedelta = dict(minutes=15)
        # Configure filters using pyes
        must = [
            pyes.TermFilter('_type', 'event'),
            pyes.TermFilter('eventsource', 'systemslogs'),
            pyes.ExistsFilter('details.sourceipaddress'),
            pyes.QueryFilter(pyes.MatchQuery('summary','failed','phrase')),
            pyes.TermFilter('program','sshd'),
            pyes.QueryFilter(pyes.MatchQuery('summary', 'login ldap_count_entries', 'boolean'))
        ]
        must_not = [
            pyes.QueryFilter(pyes.MatchQuery('summary','10.22.8.128','phrase')),
            pyes.QueryFilter(pyes.MatchQuery('summary','10.8.75.35','phrase')),
            pyes.QueryFilter(pyes.MatchQuery('summary','208.118.237.','phrase'))
        ]
        self.filtersManual(date_timedelta, must=must, must_not=must_not)

        # Search aggregations on field 'sourceipaddress', keep X samples of events at most
        self.searchEventsAggreg('sourceipaddress', samplesLimit=10)
        # alert when >= X matching events in an aggregation
        self.walkAggregations(threshold=10)

    # Set alert properties
    def onAggreg(self, aggreg):
        # aggreg['count']: number of items in the aggregation, ex: number of failed login attempts
        # aggreg['value']: value of the aggregation field, ex: toto@example.com
        # aggreg['events']: list of events in the aggregation
        category = 'bruteforce'
        tags = ['ssh']
        severity = 'NOTICE'

        summary = ('{0} ssh bruteforce attempts by {1}'.format(aggreg['count'], aggreg['value']))
        # append first 3 hostnames
        for e in aggreg['events'][:3]:
            if 'details' in e.keys() and 'hostname' in e['details']:
                summary += ' on {0}'.format(e['_source']['details']['hostname'])

        # Create the alert object based on these properties
        return self.createAlertDict(summary, category, tags, aggreg['events'], severity)