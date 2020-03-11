# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# Copyright (c) 2014 Mozilla Corporation

import hashlib
from mozdef_util.utilities.logger import logger


class message(object):
    def __init__(self):
        self.registration = ['complianceitems']
        self.priority = 20

    def validate(self, item):
        """
            Validate that a compliance item has all the necessary keys
        """
        for key in ['target', 'policy', 'check', 'compliance',
                    'link', 'utctimestamp']:
            if key not in item:
                return False
        for key in ['level', 'name', 'url']:
            if key not in item['policy']:
                return False
        for key in ['description', 'location', 'name', 'test']:
            if key not in item['check']:
                return False
        for key in ['type', 'value']:
            if key not in item['check']['test']:
                return False
        return True

    def cleanup_item(self, item):
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
            index, with a type of last_known_state.
        """
        if not self.validate(message['details']):
            logger.error('Invalid format for complianceitem {0}'.format(message))
            return (None, None)
        # add type subcategory for filtering
        message['type'] = 'last_known_state'

        item = self.cleanup_item(message['details'])
        docidstr = 'complianceitems'
        docidstr += item['check']['ref']
        docidstr += item['check']['test']['value']
        docidstr += item['target']
        metadata['id'] = hashlib.md5(docidstr).hexdigest()
        metadata['index'] = 'complianceitems'
        return (item, metadata)
