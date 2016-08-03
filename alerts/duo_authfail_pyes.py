# Copyright (c) 2014 Mozilla Corporation
#
# Contributors:
# Anthony Verez averez@mozilla.com
# Jeff Bryner jbryner@mozilla.com
# Aaron Meihm ameihm@mozilla.com
# Michal Purzynski <mpurzynski@mozilla.com>
# Alicia Smith <asmith@mozilla.com>

from lib.alerttask import AlertTask
from lib.query_classes import SearchQuery, TermFilter, ExistsFilter, QueryFilter, MatchQuery


class AlertDuoAuthFail(AlertTask):
    def main(self):
        search_query = SearchQuery(minutes=30)

        search_query.add_must([
            TermFilter('_type', 'event'),
            TermFilter('category', 'event'),
            ExistsFilter('details.ip'),
            ExistsFilter('details.username'),
            QueryFilter(MatchQuery('details.result', 'FRAUD', 'phrase')),
        ])

        self.filtersManual(search_query)
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
