# Copyright (c) 2014 Mozilla Corporation
#
# Contributors:
# Anthony Verez averez@mozilla.com
# Jeff Bryner jbryner@mozilla.com
# Aaron Meihm ameihm@mozilla.com
# Michal Purzynski <mpurzynski@mozilla.com>
# Alicia Smith <asmith@mozilla.com>

from lib.alerttask import AlertTask
from query_models import SearchQuery, TermMatch, ExistsMatch, PhraseMatch


class AlertDuoAuthFail(AlertTask):
    def main(self):
        search_query = SearchQuery(minutes=2)

        search_query.add_must([
            TermMatch('_type', 'event'),
            TermMatch('category', 'event'),
            ExistsMatch('details.sourceipaddress'),
            ExistsMatch('details.username'),
            PhraseMatch('details.result', 'FRAUD'),
        ])

        self.filtersManual(search_query)
        self.searchEventsSimple()
        self.walkEvents()

    # Set alert properties
    def onEvent(self, event):
        category = 'duosecurity'
        tags = ['duosecurity', 'duosecuritypagerduty']
        severity = 'WARNING'
        url = "https://mana.mozilla.org/wiki/display/SECURITY/IR+Procedure%3A+DuoSecurity"

        sourceipaddress = 'unknown'
        user = 'unknown'
        x = event['_source']
        if 'details' in x:
            if 'sourceipaddress' in x['details']:
                sourceipaddress = x['details']['sourceipaddress']
            if 'username' in x['details']:
                user = x['details']['username']

        summary = 'Duo Authentication Failure: user {1} rejected and marked a Duo Authentication attempt from {0} as fraud'.format(sourceipaddress, user)

        # Create the alert object based on these properties
        return self.createAlertDict(summary, category, tags, [event], severity, url)
