from datetime import datetime, timedelta
import unittest

import alerts.geomodel.config as config
import alerts.geomodel.locality as locality
import alerts.geomodel.query as query

from tests.alerts.geomodel.util import query_interface
from tests.unit_test_suite import UnitTestSuite


class TestLocalityElasticSearch(UnitTestSuite):
    '''Tests for the `locality` module that interact with ES.
    '''

    def test_simple_query(self):
        objs = [
            {
                'type_': 'locality',
                'username': 'tester1',
                'localities': [
                    {
                        'sourceipaddress': '1.2.3.4',
                        'city': 'Toronto',
                        'country': 'CA',
                        'lastaction': datetime.utcnow(),
                        'latitude': 43.6529,
                        'longitude': -79.3849,
                        'radius': 50
                    }
                ]
            }
        ]

        for obj in objs:
            self.populate_test_event(obj)

        self.refresh(self.event_index_name)

        query_iface = query.wrap(self.es_client)
        loc_cfg = config.Localities(self.event_index_name, 30, 50.0)

        results = locality.find_all(query_iface, loc_cfg)
        usernames = [state.username for state in results]

        assert len(results) == 1
        assert usernames == ['tester1']


class TestLocality(unittest.TestCase):
    '''unit tests for the `locality` module.
    '''

    def test_find_all_retrieves_all_states(self):
        query_iface = query_interface([
            {
                'type_': 'locality',
                'username': 'tester1',
                'localities': [
                    {
                        'sourceipaddress': '1.2.3.4',
                        'city': 'Toronto',
                        'country': 'CA',
                        'lastaction': datetime.utcnow(),
                        'latitude': 43.6529,
                        'longitude': -79.3849,
                        'radius': 50
                    }
                ]
            },
            {
                'type_': 'locality',
                'username': 'tester2',
                'localities': [
                    {
                        'sourceipaddress': '4.3.2.1',
                        'city': 'San Francisco',
                        'country': 'USA',
                        'lastaction': datetime.utcnow(),
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
                'type__': 'locality',  # Should have only one underscore (_)
                'username': 'tester',
                'localities': []
            },
            # Valid State
            {
                'type_': 'locality',
                'username': 'validtester',
                'localities': []
            },
            # Invalid locality data
            {
                'type_': 'locality',
                'username': 'tester2',
                'localities': [
                    {
                        # Should be sourceipaddress; missing a 'd'
                        'sourceipadress': '1.2.3.4',
                        'city': 'San Francisco',
                        'country': 'USA',
                        'lastaction': datetime.utcnow(),
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

    def test_merge_updates_localities(self):
        from_es = [
            locality.State('locality', 'user1', [
                locality.Locality(
                    sourceipaddress='1.2.3.4',
                    city='Toronto',
                    country='CA',
                    lastaction=datetime.utcnow() - timedelta(days=3),
                    latitude=43.6529,
                    longitude=-79.3849,
                    radius=50)
            ]),
        ]

        from_events = [
            locality.State('locality', 'user1', [
                locality.Locality(
                    sourceipaddress='1.2.3.4',
                    city='Toronto',
                    country='CA',
                    lastaction=datetime.utcnow() - timedelta(minutes=30),
                    latitude=43.6529,
                    longitude=-79.3849,
                    radius=50)
            ]),
        ]

        updates = locality.merge(from_es, from_events)
        user1 = [u for u in updates if u.state.username == 'user1'][0]

        last_action = user1.state.localities[0].lastaction 
        hour_ago = datetime.utcnow() - timedelta(hours=1)

        assert user1.did_update
        assert last_action < hour_ago

    def test_merge_records_new_localities(self):
        from_es = [
            locality.State('locality', 'user1', [
                locality.Locality(
                    sourceipaddress='1.2.3.4',
                    city='Toronto',
                    country='CA',
                    lastaction=datetime.utcnow() - timedelta(days=3),
                    latitude=43.6529,
                    longitude=-79.3849,
                    radius=50)
            ]),
        ]

        from_events = [
            locality.State('locality', 'user1', [
                locality.Locality(
                    sourceipaddress='32.64.128.255',
                    city='Berlin',
                    country='DE',
                    lastaction=datetime.utcnow() - timedelta(minutes=30),
                    latitude=52.520008,
                    longitude=13.404954,
                    radius=50)
            ]),
        ]

        updates = locality.merge(from_es, from_events)
        user1 = [u for u in updates if u.state.username == 'user1'][0]
        user1_cities = [loc.city for loc in user1.state.localities]

        assert user1.did_update 
        assert sorted(user1_cities) == ['Berlin', 'Toronto']

    def test_merge_includes_new_user_states(self):
        from_es = [
            # Known user, user1
            locality.State('locality', 'user1', [
                locality.Locality(
                    sourceipaddress='1.2.3.4',
                    city='Toronto',
                    country='CA',
                    lastaction=datetime.utcnow() - timedelta(days=3),
                    latitude=43.6529,
                    longitude=-79.3849,
                    radius=50)
            ]),
        ]

        from_events = [
            # New user, user3
            locality.State('locality', 'user3', [
                locality.Locality(
                    sourceipaddress='32.64.128.255',
                    city='Berlin',
                    country='DE',
                    lastaction=datetime.utcnow() - timedelta(minutes=30),
                    latitude=52.520008,
                    longitude=13.404954,
                    radius=50)
            ]),
        ]

        updates = locality.merge(from_es, from_events)
        sorted_users = sorted([u.state.username for u in updates])
        user3 = [u for u in updates if u.state.username == 'user3'][0]

        assert user3.did_update 
        assert sorted_users == ['user1', 'user3']
