# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
# Copyright (c) 2017 Mozilla Corporation

import os
import jmespath
import yaml
from mozdef_util.utilities.toUTC import toUTC


class message(object):
    def __init__(self):
        '''
            Plugin used to fix object type discretions with cloudtrail messages
        '''
        self.registration = ['githubeventsqs']
        self.priority = 10

        with open(os.path.join(os.path.dirname(__file__), 'github_mapping.yml'), 'r') as f:
            map = f.read()

        yap = yaml.load(map)
        self.eventtypes = yap.keys()
        self.yap = yap
        del(map)

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
        if 'event' in message['details']:
            newmessage['source'] = message['details']['event']
        else:
            newmessage['source'] = 'UNKNOWN'
        if 'request_id' in message['details']:
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

        return (newmessage, metadata)
