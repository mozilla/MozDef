# Copyright (c) 2014 Mozilla Corporation
#
# Contributors:
# Anthony Verez averez@mozilla.com
# Jeff Bryner jbryner@mozilla.com
# Aaron Meihm ameihm@mozilla.com
# Michal Purzynski <mpurzynski@mozilla.com>
# Alicia Smith <asmith@mozilla.com>

from lib.alerttask import AlertTask
import pyes

class AlertDuoAuthFail(AlertTask):
    def main(self):
        # look for events in last X mins
        date_timedelta = dict(minutes=30)
        # Configure filters using pyes
        must = [
            pyes.TermFilter('_type', 'event'),
            pyes.TermFilter('category', 'event'),
            pyes.ExistsFilter('details.ip'),
            pyes.ExistsFilter('details.username'),
            pyes.QueryFilter(pyes.MatchQuery('details.result', 'FRAUD', 'phrase')),
        ]
        self.filtersManual(date_timedelta, must=must)
        self.searchEventsSimple()
        self.walkEvents()

    # Set alert properties
    def onEvent(self, event):
        category = 'event'
        severity = 'WARNING'
        url = "https://mana.mozilla.org/wiki/display/SECURITY/IR+Procedure%3A+DuoSecurity"

        sourceipaddress = 'unknown'
        user = 'unknown'
        x = event['_source']
        if 'details' in x:
            if 'ip' in x['details']:
                sourceipaddress = x['details']['ip']
            if 'username' in x['details']:
                user = x['details']['username']

        summary = 'Duo Authentication Failure: user {1} rejected and marked a Duo Authentication attempt from {0} as fraud'.format(sourceipaddress, user)

        # Create the alert object based on these properties
        return self.createAlertDict(summary, category, [], [event], severity, url)
