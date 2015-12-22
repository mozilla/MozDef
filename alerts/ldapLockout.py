#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
# Copyright (c) 2014 Mozilla Corporation
#
# Contributors:
# Jeff Bryner jbryner@mozilla.com

from lib.alerttask import AlertTask
import pyes

class ldapLockout(AlertTask):
    def main(self):
        # look for events in last x 
        date_timedelta = dict(minutes=15)
        # Configure filters
        # looking for pwdAccountLockedTime setting by admin
        must = [
            pyes.TermFilter('category', 'ldapChange'),
            pyes.TermFilter("actor", "cn=admin,dc=mozilla"),
            pyes.QueryFilter(pyes.MatchQuery('changepairs', 'replace:pwdAccountLockedTime','phrase'))
        ]
        self.filtersManual(date_timedelta, must=must)

        # Search events
        self.searchEventsSimple()
        self.walkEvents()

    # Set alert properties
    def onEvent(self, event):
        category = 'ldap'
        tags = ['ldap']
        severity = 'NOTICE'
        summary='{0} LDAP account locked'.format(event['_source']['details']['dn'])

        # Create the alert object based on these properties
        return self.createAlertDict(summary, category, tags, [event], severity)
