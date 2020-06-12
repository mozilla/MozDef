from datetime import datetime
import os
import sys


def mock_search_fn(results):
    '''Creates a search function that returns a set of results on each call.
    '''

    def search_fn(_query):
        return results['hits']

    return search_fn


class TestVPNAssignment:
    def setup(self):
        self.orig_path = os.getcwd()
        self.alerts_path = os.path.join(
            os.path.dirname(__file__),
            '../../../alerts',
        )

        sys.path.insert(0, self.alerts_path)

    def teardown(self):
        os.chdir(self.orig_path)
        sys.path.remove(self.alerts_path)

        if 'lib' in sys.modules:
            del sys.modules['lib']

    def test_alert_enriched(self):
        from alerts.plugins.vpn_assignment import enrich

        assign_results = {
            'hits': [
                {
                    '_source': {
                        'utctimestamp': datetime.utcnow(),
                        'details': {
                            'username': 'tester@mozilla.com',
                            'sourceipaddress': '1.2.3.4',
                        }
                    }
                }
            ]
        }

        alert = {
            'summary': 'test summary',
            'details': {
                'something': 'original',
                'sourceipaddress': '10.48.123.13',
            }
        }

        vpn_cidrs = [
            '123.11.0.0/16',
            '10.48.0.0/16',
        ]

        search_window_hours = 6

        search_fn = mock_search_fn(assign_results)

        enriched = enrich(alert, search_window_hours, vpn_cidrs, search_fn)

        assert enriched['details']['something'] == 'original'
        assert 'vpnassignment' in enriched['details']

        assign = enriched['details']['vpnassignment']

        assert assign.get('username') == 'tester@mozilla.com'
        assert assign.get('originalip') == '1.2.3.4'

    def test_not_vpn_ip(self):
        from alerts.plugins.vpn_assignment import enrich

        assign_results = {
            'hits': [],
        }

        alert = {
            'summary': 'test summary',
            'details': {
                'something': 'original',
                'sourceipaddress': '10.48.123.13',
            }
        }

        vpn_cidrs = [
            '123.11.0.0/16',
            # Here the IP address of the user the alert fired on is NOT in a VPN
        ]

        search_window_hours = 6

        search_fn = mock_search_fn(assign_results)

        enriched = enrich(alert, search_window_hours, vpn_cidrs, search_fn)

        assert enriched['details']['something'] == 'original'
        assert 'vpnassignment' not in enriched
