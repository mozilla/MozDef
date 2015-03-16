# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
# Copyright (c) 2014 Mozilla Corporation
#
# Contributors:
# Julien Vehent jvehent@mozilla.com
# Aaron Meihm   ameihm@mozilla.com

import hashlib
import sys


class message(object):
    def __init__(self):
        self.registration = ['complianceitems']
        self.priority = 20

    def validate(self,item):
        """
            Validate that a compliance item has all the necessary keys
        """
        for key in ['target', 'policy', 'check', 'compliance',
                    'link', 'utctimestamp']:
            if key not in item.keys():
                return False
        for key in ['level', 'name', 'url']:
            if key not in item['policy'].keys():
                return False
        for key in ['description', 'location', 'name', 'test']:
            if key not in item['check'].keys():
                return False
        for key in ['type', 'value']:
            if key not in item['check']['test'].keys():
                return False
        return True

    def cleanup_item(self,item):
        ci = {}
        ci['target'] = item['target']
        ci['policy'] = {}
        ci['policy']['level'] = item['policy']['level']
        ci['policy']['name'] = item['policy']['name']
        ci['policy']['url'] = item['policy']['url']
        ci['check'] = {}
        ci['check']['description'] = item['check']['description']
        ci['check']['location'] = item['check']['location']
        ci['check']['name'] = item['check']['name']
        ci['check']['test'] = {}
        ci['check']['test']['type'] = item['check']['test']['type']
        ci['check']['test']['value'] = item['check']['test']['value']
        ci['check']['ref'] = item['check']['ref']
        ci['compliance'] = item['compliance']
        ci['link'] = item['link']
        ci['utctimestamp'] = item['utctimestamp']
        if 'tags' in item:
            ci['tags'] = item['tags']
        return ci

    def onMessage(self, message, metadata):
        """
            The complianceitems plugin is called when an event
            is posted with a doctype 'complianceitems'.
            Compliance items are stored in the complianceitems
            index, with doctype last_known_state
        """
        if not self.validate(message['details']):
            sys.stderr.write('error: invalid format for complianceitem {0}'.format(message))
            return (None, None)
        item = self.cleanup_item(message['details'])
        docidstr = 'complianceitems'
        docidstr += item['check']['ref']
        docidstr += item['check']['test']['value']
        docidstr += item['target']
        metadata['id'] = hashlib.md5(docidstr).hexdigest()
        metadata['doc_type'] = 'last_known_state'
        metadata['index'] = 'complianceitems'
        return (item, metadata)
