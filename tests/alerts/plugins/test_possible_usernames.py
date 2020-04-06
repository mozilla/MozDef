# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# Copyright (c) 2017 Mozilla Corporation

from alerts.plugins.possible_usernames import enrich


class TestPossibleUsernames:
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
