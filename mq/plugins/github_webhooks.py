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
            if key_exists('details.username', newmessage) and key_exists('details.action', newmessage) and key_exists('details.repo_name', newmessage):
                if newmessage.get('source') == 'pull_request':
                    newmessage['summary'] = "github repo {0} received a(n) {1} action on a {2} by user {3}".format(newmessage['details']['repo_name'], newmessage['details']['action'], newmessage['source'], newmessage['details']['user'])
                else:
                    newmessage['summary'] = "github repo {0} received a {1} by user {2}".format(newmessage['details']['repo_name'], newmessage['source'], newmessage['details']['username'])
            if key_exists('details.action', newmessage):
                if newmessage.get('source') == 'security_advisory':
                    newmessage['summary'] = "Security Advisory {0} for {1} ".format(newmessage['details']['action'], newmessage['details']['alert_description'])
            if 'commit_ts' in newmessage['details']:
                newmessage['timestamp'] = newmessage['details']['commit_ts']
                newmessage['utctimestamp'] = toUTC(newmessage['details']['commit_ts']).isoformat()
        else:
            newmessage = None

        return (newmessage, metadata)
