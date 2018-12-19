# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
# Copyright (c) 2017 Mozilla Corporation

import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), "../../../mq/plugins"))
from filterlog import message


class TestFilterlog():
    def setup(self):

        self.plugin = message()
        self.msg = {}
        self.msg['summary'] = '9,,,1000000103,igb0,match,block,in,4,0x0,,6,60624,0,DF,17,udp,92,175.41.7.2,21.143.56.109,57434,33443,72'

    def test_onMessage(self):
        metadata = {}
        metadata['doc_type'] = 'event'

        expected_return_message = {
            'details': {
                'action': 'block',
                'anchor': '',
                'destinationipaddress': '21.143.56.109',
                'direction': 'in',
                'interface': 'igb0',
                'ip': {
                    'ecn': '',
                    'flags': 'DF',
                    'id': '60624',
                    'length': '92',
                    'offset': '0',
                    'protocol_id': '17',
                    'protocol_text': 'udp',
                    'tos': '0x0',
                    'ttl': '6',
                    'version': 4
                },
                'ip_version': '4',
                'reason': 'match',
                'rule_number': '9',
                'sourceipaddress': '175.41.7.2',
                'sub_rule_number': '',
                'trackor': '1000000103',
                'data_length': '72',
                'destination_port': '33443',
                'source_port': '57434'
            },
            'summary': '9,,,1000000103,igb0,match,block,in,4,0x0,,6,60624,0,DF,17,udp,92,175.41.7.2,21.143.56.109,57434,33443,72'
        }

        (retmessage, retmeta) = self.plugin.onMessage(self.msg, metadata)
        assert retmessage == expected_return_message
