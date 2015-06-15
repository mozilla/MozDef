# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
# Copyright (c) 2015 Mozilla Corporation
#
# Contributors:
# Guillaume Destuynder gdestuynder@mozilla.com
# Aaron Meihm ameihm@mozilla.com

import hashlib
import sys
import unittest

class message(object):
    def __init__(self):
        self.registration = ['rra']
        self.priority = 20

    def validate_field(self, field, keys):
        for k in keys:
            if not k in field.keys():
                return False
        return True

    def validate(self, message):
        if not self.validate_field(message, ['details', 'utctimestamp', 'summary', 'source', 'lastmodified']):
            return False
        if not self.validate_field(message['details'], ['data', 'risk', 'metadata']):
            return false
        if not self.validate_field(message['details']['metadata'], ['operator', 'scope', 'owner', 'developer',
            'service', 'description']):
            return False
        if not self.validate_field(message['details']['data'], ['Unknown', 'PUBLIC', 'INTERNAL', 'RESTRICTED', 'SECRET',
            'default']):
            return False
        if not self.validate_field(message['details']['risk'], ['integrity', 'confidentiality', 'availability']):
            return False
        for f in ['integrity', 'confidentiality', 'availability']:
            if not self.validate_field(message['details']['risk'][f], ['rationale', 'impact', 'probability']):
                return False

        if (len(message['details']['metadata']['service']) == 0):
            return False
        if (message['details']['metadata']['service'] == 'RRA for '):
            return False

        return True

    def calculate_id(self, message):
        s = '{0}|{1}'.format(message['source'], message['lastmodified'])
        return hashlib.sha256(s.encode('ascii')).hexdigest()

    def onMessage(self, message, metadata):
        if metadata['doc_type'] != 'rra':
            return (message, metadata)
        if not self.validate(message):
            sys.stderr.write('error: invalid format for RRA {0}'.format(message))
            return (None, None)
        metadata['id'] = self.calculate_id(message)
        metadata['doc_type'] = 'rra_state'
        metadata['index'] = 'rra'
        return (message, metadata)

class MessageTestFunctions(unittest.TestCase):
    def setUp(self):
        self.msgobj = message()

        self.msg = {}
        self.msg['utctimestamp'] = '2015-06-12T23:00:18.381000+00:00'
        self.msg['summary'] = 'an RRA event'
        self.msg['category'] = 'rra_data'
        self.msg['source'] = '1U_zcHwal1lCtLK-cwYHuTp6x1jWho_0FN-2remYQSEY'
        self.msg['lastmodified'] = '2015-06-11T23:00:18.381000+00:00'
        self.msg['details'] = {}
        self.msg['details']['metadata'] = {}
        self.msg['details']['metadata']['service'] = 'TestService Name'
        self.msg['details']['metadata']['operator'] = 'IT'
        self.msg['details']['metadata']['owner'] = 'IT'
        self.msg['details']['metadata']['developer'] = '3rd party'
        self.msg['details']['metadata']['scope'] = ''
        self.msg['details']['metadata']['description'] = ''
        self.msg['details']['risk'] = {}
        self.msg['details']['risk']['integrity'] = {}
        self.msg['details']['risk']['integrity']['rationale'] = {}
        self.msg['details']['risk']['integrity']['impact'] = {}
        self.msg['details']['risk']['integrity']['probability'] = {}
        self.msg['details']['risk']['availability'] = {}
        self.msg['details']['risk']['availability']['rationale'] = {}
        self.msg['details']['risk']['availability']['impact'] = {}
        self.msg['details']['risk']['availability']['probability'] = {}
        self.msg['details']['risk']['confidentiality'] = {}
        self.msg['details']['risk']['confidentiality']['rationale'] = {}
        self.msg['details']['risk']['confidentiality']['impact'] = {}
        self.msg['details']['risk']['confidentiality']['probability'] = {}
        self.msg['details']['data'] = {}
        self.msg['details']['data']['Unknown'] = {}
        self.msg['details']['data']['PUBLIC'] = {}
        self.msg['details']['data']['INTERNAL'] = {}
        self.msg['details']['data']['RESTRICTED'] = {}
        self.msg['details']['data']['SECRET'] = {}
        self.msg['details']['data']['default'] = ''

    def test_onMessage(self):
        metadata = {}
        metadata['doc_type'] = 'rra'
        (retmessage, retmeta) = self.msgobj.onMessage(self.msg, metadata)
        self.assertIsNotNone(retmessage)
        self.assertIsNotNone(retmeta)
        self.assertEqual(retmeta['id'], '9ee7fb9244a61e681df89ae5bf3040e33f7471316a03cf421754f8be2bec08b2')

    def test_calculate_id(self):
        self.assertEqual(self.msgobj.calculate_id(self.msg),
                '9ee7fb9244a61e681df89ae5bf3040e33f7471316a03cf421754f8be2bec08b2')

    def test_validate_correct(self):
        self.assertTrue(self.msgobj.validate(self.msg))

    def test_validate_incorrect(self):
        del self.msg['utctimestamp']
        self.assertFalse(self.msgobj.validate(self.msg))

    def test_validate_incorrect_vuln(self):
        del self.msg['details']['metadata']['service']
        self.assertFalse(self.msgobj.validate(self.msg))

if __name__ == '__main__':
    unittest.main(verbosity=2)
