#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# Copyright (c) 2014 Mozilla Corporation
#
# This script alerts when openvpn's duo security failed to contact the duo server and let the user in.
# This is a very serious warning that must be acted upon as it means MFA failed and only one factor was validated (in
# this case a VPN certificate)

from lib.alerttask import AlertTask
from mozdef_util.query_models import SearchQuery, PhraseMatch


class AlertDuoFailOpen(AlertTask):
    def main(self):
        search_query = SearchQuery(minutes=15)

        search_query.add_must(PhraseMatch('summary', 'Failsafe Duo login'))

        self.filtersManual(search_query)

        # Search aggregations on field 'sourceipaddress', keep X samples of
        # events at most
        self.searchEventsAggregated('hostname', samplesLimit=10)
        # alert when >= X matching events in an aggregation
        # in this case, always
        self.walkAggregations(threshold=1)

    # Set alert properties
    def onAggregation(self, aggreg):
        # aggreg['count']: number of items in the aggregation, ex: number of failed login attempts
        # aggreg['value']: value of the aggregation field, ex: toto@example.com
        # aggreg['events']: list of events in the aggregation
        category = 'bypass'
        tags = ['openvpn', 'duosecurity']
        severity = 'WARNING'

        summary = 'DuoSecurity contact failed, fail open triggered on {0}'.format(aggreg['value'])

        # Create the alert object based on these properties
        return self.createAlertDict(summary, category, tags, aggreg['events'], severity)
