# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
# Copyright (c) 2017 Mozilla Corporation

import os
import sys

plugin_path = os.path.join(os.path.dirname(__file__), '../../../alerts/plugins')
sys.path.append(plugin_path)

from port_scan_enrichment import enrich


EXAMPLE_TIMESTAMP = '2016-07-13 22:33:31.625443+00:00'


def mock_search_fn(results):
    def search_fn(_query):
        return results

    return search_fn


class TestPortScanEnrichment(object):
    def test_alert_enriched(self):
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
            'details': {
                'sourceipaddress': '127.0.0.1'
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
