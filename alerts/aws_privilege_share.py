from functools import reduce
import json
import os

from lib.alerttask import AlertTask
from mozdef_util.query_models import SearchQuery, TermMatch, QueryStringMatch


_CONFIG_FILE = os.path.join(
    os.path.dirname(__file__),
    'aws_privilege_share.json')

_AGGREGATE_KEY = 'details.requestparameters.username'

_IAM_USER_KEY = 'details.useridentity.sessioncontext.sessionissuer.username'

_AWS_EVENT_KEY = 'details.eventname'

_ATTACH_POLICY_ACTION = 'AttachUserPolicy'


class AlertAWSPrivilegeShare(AlertTask):
    '''An alert that fires when any of a configured list of AWS IAM users
    perform the AttachUserPolicy action on another user.  Such activity may
    indicate that root privileges are being shared.
    '''

    def main(self):
        with open(_CONFIG_FILE) as cfg_file:
            self.config = json.load(cfg_file)

        query_string = ' OR '.join([
            '{0}: {1}'.format(_IAM_USER_KEY, user)
            for user in self.config['rootUsers']
        ])

        query = SearchQuery(**self.config['searchWindow'])
        query.add_must([
            QueryStringMatch(query_string),
            TermMatch(_AWS_EVENT_KEY, _ATTACH_POLICY_ACTION)
        ])

        self.filtersManual(query)
        self.searchEventsAggregated(_AGGREGATE_KEY, samplesLimit=10)
        self.walkAggregations(threshold=1)

    def onAggregation(self, aggreg):
        # Index all the way into the first event to get the name of the IAM
        # user that attached a new policy to another user.
        issuing_user = reduce(
            lambda d, k: d and d.get(k),
            _IAM_USER_KEY.split('.'),
            aggreg['events'][0])

        summary = '{0} granted permissions to {1} in AWS'.format(
            issuing_user,
            aggreg['value'])
        category = 'privileges'
        tags = ['aws', 'privileges']
        events = aggreg['events']
        severity = 'NOTICE'

        return self.createAlertDict(summary, category, tags, events, severity)
