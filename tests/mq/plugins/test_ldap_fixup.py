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
                'actor': 'o=com,mail=tester@mozilla.com,dc=mozilla'
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
                'email': 'tester@mozilla.com',
                'username': 'tester',
                'actor': 'o=com,mail=tester@mozilla.com,dc=mozilla'
            }
        }
        assert retmessage == expected_message
        assert retmeta == {}

    def test_ldap_fixup_complex_actor_format(self):
        msg = {
            'summary': 'LDAP-Humanizer:45582:1.1.1.1',
            'hostname': 'random.host.com',
            'category': 'ldap',
            'details': {
                'tls': 'true',
                'authenticated': 'true',
                'actor': 'dc=mozilla mail=tester@mozilla.com,o=com,dc=mozilla '
                'IP=123.45.67.89:46740 conn=180255',
            }
        }

        expected = {
            'summary': 'LDAP-Humanizer:45582:1.1.1.1',
            'hostname': 'random.host.com',
            'category': 'ldap',
            'source': 'ldap',
            'details': {
                'tls_encrypted': 'true',
                'authenticated': 'true',
                'email': 'tester@mozilla.com',
                'username': 'tester',
                'actor': 'dc=mozilla mail=tester@mozilla.com,o=com,dc=mozilla '
                'IP=123.45.67.89:46740 conn=180255',
            }
        }

        (retmessage, retmeta) = self.plugin.onMessage(msg, {})

        assert retmessage == expected
        assert retmeta == {}

    def test_ldap_fixup_missing_actor(self):
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

        assert retmessage['details'].get('email') is None
        assert retmessage['details'].get('username') is None

    def test_ldap_fixup_poorly_formatted_actor(self):
        msgs = [
            {
                'summary': 'LDAP-Humanizer:45582:1.1.1.1',
                'hostname': 'random.host.com',
                'category': 'ldap',
                'details': {
                    'tls': 'true',
                    'authenticated': 'true',
                    'actor': 'o=com=extra,mail=tester@mozilla.com=extra2',
                }
            },
            {
                'summary': 'LDAP-Humanizer:45582:1.1.1.1',
                'hostname': 'random.host.com',
                'category': 'ldap',
                'details': {
                    'tls': 'true',
                    'authenticated': 'true',
                    'actor': 'o=com,',
                }
            },
            {
                'summary': 'LDAP-Humanizer:45582:1.1.1.1',
                'hostname': 'random.host.com',
                'category': 'ldap',
                'details': {
                    'tls': 'true',
                    'authenticated': 'true',
                    'actor': 'o,mail',
                }
            }
        ]

        for msg in msgs:
            (retmessage, retmeta) = self.plugin.onMessage(msg, {})

            assert retmessage['details'].get('email') is None
            assert retmessage['details'].get('username') is None
