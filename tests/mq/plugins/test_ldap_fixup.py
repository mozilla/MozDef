# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# Copyright (c) 2017 Mozilla Corporation

from mq.plugins.zoom_fixup import message


class TestLdapFixupPlugin():
    def setup(self):
        self.plugin = message()

    def test_details_tls_rename(self):
        msg = {
            'summary': 'LDAP-Humanizer:45582:1.1.1.1',
            'hostname': 'random.host.com',
            'details': {
                'tls': 'true',
                'authenticated': 'true',
            }
        }
        (retmessage, retmeta) = self.plugin.onMessage(msg, {})

        expected_message = {
            'summary': 'LDAP-Humanizer:45582:1.1.1.1',
            'hostname': 'random.host.com',
            'details': {
                'tls_encrypted': 'true',
                'authenticated': 'true',
            }
        }
        assert retmessage == expected_message
        assert retmeta == {}

    def test_source_addition(self):
        msg = {
            'summary': 'LDAP-Humanizer:45582:1.1.1.1',
            'hostname': 'random.host.com',
            'details': {
                'tls': 'true',
                'authenticated': 'true',
            }
        }
        (retmessage, retmeta) = self.plugin.onMessage(msg, {})

        expected_message = {
            'summary': 'LDAP-Humanizer:45582:1.1.1.1',
            'hostname': 'random.host.com',
            'source': 'ldap',
            'details': {
                'tls': 'true',
                'authenticated': 'true',
            }
        }
        assert retmessage == expected_message
        assert retmeta == {}
