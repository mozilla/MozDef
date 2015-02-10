# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
# Copyright (c) 2014 Mozilla Corporation
#
# Contributors:
# Julien Vehent jvehent@mozilla.com

import hashlib
import sys


class message(object):
    def __init__(self):
        self.registration = ['complianceitems']
        self.priority = 20

    def validate(self,message):
        """
            Validate that a compliance item has all the necessary keys
        """
        for key in ['target', 'policy', 'check', 'compliance',
                    'link', 'utctimestamp']:
            if key not in message.keys():
                return False
        for key in ['level', 'name', 'url']:
            if key not in message['policy'].keys():
                return False
        for key in ['description', 'location', 'name', 'test']:
            if key not in message['check'].keys():
                return False
        for key in ['type', 'value']:
            if key not in message['check']['test'].keys():
                return False
        return True

    def cleanup_item(self,message):
        ci = {}
        ci['target'] = message['target']
        ci['policy'] = {}
        ci['policy']['level'] = message['policy']['level']
        ci['policy']['name'] = message['policy']['name']
        ci['policy']['url'] = message['policy']['url']
        ci['check'] = {}
        ci['check']['description'] = message['check']['description']
        ci['check']['location'] = message['check']['location']
        ci['check']['name'] = message['check']['name']
        ci['check']['test'] = {}
        ci['check']['test']['type'] = message['check']['test']['type']
        ci['check']['test']['value'] = message['check']['test']['value']
        ci['check']['ref'] = message['check']['ref']
        ci['compliance'] = message['compliance']
        ci['link'] = message['link']
        ci['utctimestamp'] = message['utctimestamp']
        if 'tags' in message:
            ci['tags'] = message['tags']
        return ci

    def onMessage(self, message, metadata):
        """
            The complianceitems plugin is called when an event
            is posted with a doctype 'complianceitems'.
            Compliance items are stored in the complianceitems
            index, with doctype last_known_state
        """
        if metadata['doc_type'] == 'complianceitems':
            if not self.validate(message):
                sys.stderr.write('error: invalid format for complianceitem {0}'.format(message))
                return (None, None)
            message = self.cleanup_item(message)
            docidstr = 'complianceitems'
            docidstr += message['check']['ref']
            docidstr += message['check']['test']['value']
            docidstr += message['target']
            metadata['id'] = hashlib.md5(docidstr).hexdigest()
            metadata['doc_type'] = 'last_known_state'
            metadata['index'] = 'complianceitems'
        return (message, metadata)
