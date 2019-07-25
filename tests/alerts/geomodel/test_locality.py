from datetime import datetime
import unittest

import alerts.geomodel.config as config
import alerts.geomodel.locality as locality

from tests.alerts.geomodel.util import query_interface


class TestLocality(unittest.TestCase):
    '''unit tests for the `locality` module.
    '''

    def test_find_all_retrieves_all_states(self):
        query_iface = query_interface([
            {
                'type_': 'geomodel',
                'username': 'tester1',
                'localities': [
                    {
                        'sourceipv4address': '1.2.3.4',
                        'city': 'Toronto',
                        'country': 'CA',
                        'lastaction': datetime.now(),
                        'latitude': 43.6529,
                        'longitude': -79.3849,
                        'radius': 50
                    }
                ]
            },
            {
                'type_': 'geomodel',
                'username': 'tester2',
                'localities': [
                    {
                        'sourceipv4address': '4.3.2.1',
                        'city': 'San Francisco',
                        'country': 'USA',
                        'lastaction': datetime.now(),
                        'latitude': 37.773972,
                        'longitude': -122.431297,
                        'radius': 50
                    }
                ]
            }
        ])
        loc_cfg = config.Localities('localities', 30, 50.0)

        results = locality.find_all(query_iface, loc_cfg)
        usernames = [state.username for state in results]

        assert len(results) == 2
        assert 'tester1' in usernames
        assert 'tester2' in usernames
        assert len(results[0].localities) == 1
        assert len(results[1].localities) == 1

    def test_find_all_ignores_invalid_data(self):
        query_iface = query_interface([
            # Invalid top-level State
            {
                'type__': 'geomodel',  # Should have only one underscore (_)
                'username': 'tester',
                'localities': []
            },
            # Valid State
            {
                'type_': 'geomodel',
                'username': 'validtester',
                'localities': []
            },
            # Invalid locality data
            {
                'type_': 'geomodel',
                'username': 'tester2',
                'localities': [
                    {
                        # Should be sourceipv4address
                        'sourceipaddress': '1.2.3.4',
                        'city': 'San Francisco',
                        'country': 'USA',
                        'lastaction': datetime.now(),
                        'latitude': 37.773972,
                        'longitude': -122.431297,
                        'radius': 50
                    }
                ]
            }
        ])
        loc_cfg = config.Localities('localities', 30, 50.0)

        results = locality.find_all(query_iface, loc_cfg)
        usernames = [state.username for state in results]

        assert len(results) == 1
        assert usernames == ['validtester']
