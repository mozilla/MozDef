# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# Copyright (c) 2017 Mozilla Corporation

import os
import jmespath
import yaml
from mozdef_util.utilities.toUTC import toUTC
from mozdef_util.utilities.key_exists import key_exists


class message(object):
    def __init__(self):
        '''
            Plugin used to fix object type discretions with cloudtrail messages
        '''
        self.registration = ['githubeventsqs']
        self.priority = 10

        with open(os.path.join(os.path.dirname(__file__), 'github_mapping.yml'), 'r') as f:
            mapping_map = f.read()

        yap = yaml.safe_load(mapping_map)
        self.eventtypes = list(yap.keys())
        self.yap = yap
        del(mapping_map)

    def onMessage(self, message, metadata):

        if 'tags' not in message:
            return (message, metadata)
        if 'githubeventsqs' not in message['tags']:
            return (message, metadata)

        newmessage = {}
        newmessage['details'] = {}

        newmessage['category'] = 'github'
        newmessage['tags'] = ['github', 'webhook']
        newmessage['eventsource'] = 'githubeventsqs'

        if key_exists('details.event', message):
            newmessage['source'] = message['details']['event']
        else:
            newmessage['source'] = 'UNKNOWN'
        if key_exists('details.request_id', message):
            newmessage['details']['request_id'] = message['details']['request_id']
        else:
            newmessage['details']['request_id'] = 'UNKNOWN'

        # iterate through top level keys - push, etc
        if newmessage['source'] in self.eventtypes:
            for key in self.yap[newmessage['source']]:
                mappedvalue = jmespath.search(self.yap[newmessage['source']][key], message)
                # JMESPath likes to silently return a None object
                if mappedvalue is not None:
                    newmessage['details'][key] = mappedvalue
            if 'commit_ts' in newmessage['details']:
                newmessage['timestamp'] = newmessage['details']['commit_ts']
                newmessage['utctimestamp'] = toUTC(newmessage['details']['commit_ts']).isoformat()

        else:
            newmessage = None

        if key_exists('source', newmessage) and newmessage.get('source') is not 'UNKNOWN':
            newmessage['summary'] = "github: {0}: ".format(newmessage['source'])
            if key_exists('source', newmessage) and newmessage.get('source') is 'installation':
                newmessage['summary'] = "github app: {0} ".format(newmessage['source'])
            if key_exists('source', newmessage) and newmessage.get('source') is 'public':
                newmessage['summary'] = "github : change from private to {0} ".format(newmessage['source'])
        if key_exists('details.status', newmessage):
            action_status = "{0} ".format(newmessage['details']['status'])
            newmessage['summary'] += action_status
        if key_exists('details.action', newmessage):
            github_action = "{0} ".format(newmessage['details']['action'])
            newmessage['summary'] += github_action
        if key_exists('details.ref_type', newmessage):
            reference = "{0} ".format(newmessage['details']['ref_type'])
            newmessage['summary'] += reference
        if key_exists('details.repo_name', newmessage):
            repository_name = "on repo: {0} ".format(newmessage['details']['repo_name'])
            newmessage['summary'] += repository_name
        if key_exists('details.alert_note', newmessage):
            sec_advisory = "for: {0}".format(newmessage['details']['alert_note'])
            newmessage['summary'] += sec_advisory
        if key_exists('details.alert_package', newmessage):
            vuln_package = "package: {0} ".format(newmessage['details']['alert_package'])
            newmessage['summary'] += vuln_package
        if key_exists('details.team_name', newmessage):
            team_name = "team: {0} ".format(newmessage['details']['team_name'])
            newmessage['summary'] += team_name
        if key_exists('details.blocked_user_login', newmessage):
            blocked_user = "user: {0} ".format(newmessage['details']['blocked_user_login'])
            newmessage['summary'] += blocked_user
        if key_exists('details.org_login', newmessage):
            org_name = "in org: {0} ".format(newmessage['details']['org_login'])
            newmessage['summary'] += org_name
        if key_exists('details.username', newmessage):
            github_user = "user: {0}".format(newmessage['details']['username'])
            newmessage['summary'] += "triggered by " + github_user

        return (newmessage, metadata)
