# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# Copyright (c) 2017 Mozilla Corporation

import os
import sys

EXAMPLE_TIMESTAMP = '2016-07-13 22:33:31.625443+00:00'


def mock_search_fn(results):
    def search_fn(_query):
        return results

    return search_fn


class TestPortScanEnrichment():
    def teardown(self):
        os.chdir(self.orig_path)
        sys.path.remove(self.alerts_path)
        if 'lib' in sys.modules:
            del sys.modules['lib']

    def setup(self):
        self.orig_path = os.getcwd()
        self.alerts_path = os.path.join(os.path.dirname(__file__), "../../../alerts")
        sys.path.insert(0, self.alerts_path)

    def test_alert_enriched(self):
        from alerts.plugins.port_scan_enrichment import enrich
        results = {
            'hits': [
                {
                    '_source': {
                        'details': {
                            'destinationipaddress': '1.2.3.4',
                            'destinationport': 80
                        },
                        'timestamp': EXAMPLE_TIMESTAMP
                    }
                },
                {
                    '_source': {
                        'details': {
                            'destinationipaddress': '4.3.2.1',
                            'destinationport': 443
                        },
                        'timestamp': EXAMPLE_TIMESTAMP
                    }
                }
            ]
        }

        alert = {
            'events': [
                {
                    'documentsource': {
                        'details': {
                            'sourceipaddress': '127.0.0.1'
                        },
                    }
                }
            ],
            'details': {
                'something': 'original'
            }
        }

        search_window = {
            'hours': 1
        }

        max_conns = 1

        enriched = enrich(
            alert,
            mock_search_fn(results),
            search_window,
            max_conns)

        assert len(enriched['details']['recentconnections']) == 1
        assert enriched['details']['recentconnections'][0]['destinationipaddress'] in ['1.2.3.4', '4.3.2.1']
        assert enriched['details']['recentconnections'][0]['destinationport'] in [80, 443]
        assert enriched['details']['recentconnections'][0]['timestamp'] == EXAMPLE_TIMESTAMP
        assert enriched['details']['something'] == 'original'
