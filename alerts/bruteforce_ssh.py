#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
# Copyright (c) 2014 Mozilla Corporation
#
# Contributors:
# Anthony Verez averez@mozilla.com

from lib.alerttask import AlertTask

class AlertBruteforceSsh(AlertTask):
    def main(self):
    	# Configure filters by importing a kibana dashboard
    	date_timedelta = dict(minutes=15)
    	self.filtersFromKibanaDash('mozilla_bruteforce_ssh_dashboard.json', date_timedelta)

    	# Search aggregations on field 'sourceipaddress'
    	self.searchEventsAggreg('sourceipaddress', samplesLimit=50)
        # alert when >= 5 matching events in an aggregation
    	self.walkAggregations(threshold=2)

    # Set alert properties
    def onAggreg(self, aggreg):
    	category = 'bruteforce'
    	tags = ['ssh']
    	severity = 'NOTICE'

        summary = ('{0} ssh bruteforce attempts by {1}'.format(aggreg['count'], aggreg['value']))
        for e in aggreg['events'][:3]:
            if 'details' in e.keys() and 'hostname' in e['details']:
                summary += ' on {0}'.format(e['_source']['details']['hostname'])

        # Create the alert object based on these properties
    	return self.createAlertDict(summary, category, tags, aggreg['events'], severity)
