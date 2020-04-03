# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# Copyright (c) 2017 Mozilla Corporation

from alerts.plugins.geomodel_ipintel_enrichment import enrich


class TestGeoModelEnrichment:
    def test_enrichment(self):
        test_alert = {
            'summary': 'test alert',
            'details': {
                'hops': [
                    {
                        'origin': {
                            'ip': '1.2.3.4',
                        },
                        'destination': {
                            'ip': '4.3.2.1',
                        }
                    },
                    {
                        'origin': {
                            'ip': '4.3.2.1',
                        },
                        'destination': {
                            'ip': '1.4.2.3',
                        }
                    },
                    {
                        'origin': {
                            'ip': '1.4.2.3',
                        },
                        'destination': {
                            'ip': '1.2.3.4',
                        }
                    }
                ]
            }
        }

        test_intel = {
            '1.2.3.4': {
                'TorNode': 127,
            },
            '4.3.2.1': {
                'Spam': 32,
                'VPN': 80,
            }
        }

        enriched = enrich(test_alert, test_intel)

        # Make sure nothing previously present was changed.
        assert 'details' in enriched
        assert 'hops' in enriched['details']
        assert len(enriched['details']['hops']) == 3

        # Make sure info for the known IPs was added.
        assert 'ipintel' in enriched['details']
        assert len(enriched['details']['ipintel']) == 3
        assert {
            'ip': '1.2.3.4',
            'classification': 'TorNode',
            'threatscore': 127
        } in enriched['details']['ipintel']
        assert {
            'ip': '4.3.2.1',
            'classification': 'Spam',
            'threatscore': 32
        } in enriched['details']['ipintel']
        assert {
            'ip': '4.3.2.1',
            'classification': 'VPN',
            'threatscore': 80
        } in enriched['details']['ipintel']

        # Make sure that the alert summary was appended to.
        assert 'Tor nodes detected: 1.2.3.4' in enriched['summary']
        assert 'VPNs detected: 4.3.2.1' in enriched['summary']
