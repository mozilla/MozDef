import os
import json

from lib.alerttask import AlertTask
from mozdef_util.query_models import SearchQuery, QueryStringMatch


_CONFIG_FILE = os.path.join(
    os.path.dirname(__file__),
    'sensitiveuser_uid0.json')


class AlertSensitiveUserUID0(AlertTask):
    '''Alert when an event is observed to have been triggered by any of a
    configured list of users with uid 0.
    '''

    def main(self):
        '''Search for events triggered by any of a configured list of users.
        '''

        with open(_CONFIG_FILE) as cfg_file:
            self.config = json.load(cfg_file)

        user_conditions = ' OR '.join([
            'details.user: {}'.format(user)
            for user in self.config['sensitiveUsers']
        ])
        lucene_query = 'details.uid: 0 AND (' + user_conditions + ')'

        query = SearchQuery(**self.config['searchWindow'])
        query.add_must(QueryStringMatch(lucene_query))

        self.filtersManual(query)
        self.searchEventsSimple()
        self.walkEvents()

    def onEvent(self, event):
        '''Construct an alert for each event found.
        '''

        category = 'anomaly'
        tags = ['uid0', 'anomaly']
        severity = 'CRITICAL'
        summary = 'User {0} with uid 0 active on host {1}'.format(
            event['_source']['details']['user'],
            event['_source']['hostname'])

        return self.createAlertDict(summary, category, tags, [event], severity)
