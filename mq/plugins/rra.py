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
                sys.stderr.write('warning: key {0} not in expected list {1}\n'.format(k, field.keys()))
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
        for cia in ['integrity', 'confidentiality', 'availability']:
            for rpf in ['productivity', 'finances', 'reputation']:
                if not self.validate_field(message['details']['risk'][cia][rpf], ['rationale', 'impact', 'probability']):
                    return False

        if (len(message['details']['metadata']['service']) == 0):
            sys.stderr.write('warning: no service name for {0}\n'.format(message['source']))
            return False
        if (message['details']['metadata']['service'] == 'RRA for '):
            sys.stderr.write('warning: Invalid service name for {0}\n'.format(message['source']))
            return False

        return True

    def calculate_id(self, message):
        s = '{0}|{1}'.format(message['source'], message['lastmodified'])
        return hashlib.sha256(s.encode('ascii')).hexdigest()

    def onMessage(self, message, metadata):
        if metadata['doc_type'] != 'rra':
            return (message, metadata)
        if not self.validate(message):
            sys.stderr.write('error: invalid format for RRA {0}\n'.format(message))
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
        self.msg['details']['risk']['integrity']['reputation'] = {}
        self.msg['details']['risk']['integrity']['reputation']['rationale'] = ''
        self.msg['details']['risk']['integrity']['reputation']['impact'] = ''
        self.msg['details']['risk']['integrity']['reputation']['probability'] = ''
        self.msg['details']['risk']['integrity']['productivity'] = {}
        self.msg['details']['risk']['integrity']['productivity']['impact'] = ''
        self.msg['details']['risk']['integrity']['productivity']['rationale'] = ''
        self.msg['details']['risk']['integrity']['productivity']['probability'] = ''
        self.msg['details']['risk']['integrity']['finances'] = {}
        self.msg['details']['risk']['integrity']['finances']['probability'] = ''
        self.msg['details']['risk']['integrity']['finances']['impact'] = ''
        self.msg['details']['risk']['integrity']['finances']['rationale'] = ''
        self.msg['details']['risk']['availability'] = {}
        self.msg['details']['risk']['availability']['productivity'] = {}
        self.msg['details']['risk']['availability']['productivity']['rationale'] = ''
        self.msg['details']['risk']['availability']['productivity']['impact'] = ''
        self.msg['details']['risk']['availability']['productivity']['probability'] = ''
        self.msg['details']['risk']['availability']['finances'] = {}
        self.msg['details']['risk']['availability']['finances']['impact'] = ''
        self.msg['details']['risk']['availability']['finances']['rationale'] = ''
        self.msg['details']['risk']['availability']['finances']['probability'] = ''
        self.msg['details']['risk']['availability']['reputation'] = {}
        self.msg['details']['risk']['availability']['reputation']['probability'] = ''
        self.msg['details']['risk']['availability']['reputation']['impact'] = ''
        self.msg['details']['risk']['availability']['reputation']['rationale'] = ''
        self.msg['details']['risk']['confidentiality'] = {}
        self.msg['details']['risk']['confidentiality']['finances']= {}
        self.msg['details']['risk']['confidentiality']['finances']['rationale'] = ''
        self.msg['details']['risk']['confidentiality']['finances']['impact'] = ''
        self.msg['details']['risk']['confidentiality']['finances']['probability'] = ''
        self.msg['details']['risk']['confidentiality']['reputation'] = {}
        self.msg['details']['risk']['confidentiality']['reputation']['impact'] = ''
        self.msg['details']['risk']['confidentiality']['reputation']['rationale'] = ''
        self.msg['details']['risk']['confidentiality']['reputation']['probability'] = ''
        self.msg['details']['risk']['confidentiality']['productivity'] = {}
        self.msg['details']['risk']['confidentiality']['productivity']['probability'] = ''
        self.msg['details']['risk']['confidentiality']['productivity']['rationale'] = ''
        self.msg['details']['risk']['confidentiality']['productivity']['impact'] = ''
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
