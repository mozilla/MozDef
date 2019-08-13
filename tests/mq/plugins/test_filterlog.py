# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# Copyright (c) 2017 Mozilla Corporation

from mq.plugins.filterlog import message


class TestFilterlog():
    def setup(self):

        self.plugin = message()
        self.msg = {}
        self.msg['summary'] = '9,,,1000000103,igb0,match,block,in,4,0x0,,6,60624,0,DF,17,udp,92,175.41.7.2,21.143.56.109,57434,33443,72'

    def test_onMessage(self):
        metadata = {}

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
                    'protocolid': '17',
                    'protocoltext': 'udp',
                    'tos': '0x0',
                    'ttl': '6',
                    'version': 4
                },
                'ipversion': '4',
                'reason': 'match',
                'rulenumber': '9',
                'sourceipaddress': '175.41.7.2',
                'subrulenumber': '',
                'trackor': '1000000103',
                'datalength': '72',
                'destinationport': '33443',
                'sourceport': '57434'
            },
            'summary': '9,,,1000000103,igb0,match,block,in,4,0x0,,6,60624,0,DF,17,udp,92,175.41.7.2,21.143.56.109,57434,33443,72'
        }

        (retmessage, retmeta) = self.plugin.onMessage(self.msg, metadata)
        assert retmessage == expected_return_message
