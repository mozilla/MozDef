# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# Copyright (c) 2017 Mozilla Corporation

from mq.plugins.ldap_fixup import message


class TestLdapFixupPlugin():
    def setup(self):
        self.plugin = message()

    def test_ldap_fixup_plugin(self):
        msg = {
            'summary': 'LDAP-Humanizer:45582:1.1.1.1',
            'hostname': 'random.host.com',
            'category': 'ldap',
            'details': {
                'tls': 'true',
                'authenticated': 'true',
            }
        }
        (retmessage, retmeta) = self.plugin.onMessage(msg, {})

        expected_message = {
            'summary': 'LDAP-Humanizer:45582:1.1.1.1',
            'hostname': 'random.host.com',
            'category': 'ldap',
            'source': 'ldap',
            'details': {
                'tls_encrypted': 'true',
                'authenticated': 'true',
            }
        }
        assert retmessage == expected_message
        assert retmeta == {}
