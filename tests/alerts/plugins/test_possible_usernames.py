# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# Copyright (c) 2017 Mozilla Corporation

import os
import sys

from alerts.plugins.possible_usernames import enrich


class TestPossibleUsernames:
    def setup(self):
        self._orig_path = os.getcwd()

        self._alerts_path = os.path.join(
            os.path.dirname(__file__),
            '../../../alerts')

        sys.path.insert(0, self._alerts_path)

    def teardown(self):
        os.chdir(self._orig_path)

        sys.path.remove(self._alerts_path)

        if 'lib' in sys.modules:
            del sys.modules['lib']

    def test_enrichment(self):
        events = [
            {
                # Expected event
                'details': {
                    'username': 'tester1'
                }
            },
            {
                # No username
                'details': {
                    'otherthing': 'somevalue'
                }
            },
            {
                # No details
                'notwhatwewant': {
                    'something': 'else'
                }
            },
            {
                # Duplicate user
                'details': {
                    'username': 'tester1'
                }
            }
        ]

        alert = {
            'details': {
                'username': 'tester2'
            }
        }

        enriched = enrich(alert, events)

        # Ensure old fields still present.
        assert enriched['details']['username'] == 'tester2'

        # Ensure possible users found and duplicates removed.
        assert len(enriched['details']['possible_usernames']) == 1
        assert enriched['details']['possible_usernames'][0] == 'tester1'
