from datetime import datetime, timedelta
import unittest

import alerts.geomodel.config as config
import alerts.geomodel.event as event 
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

        entries = locality.find_all(query_iface, loc_cfg)
        usernames = [entry.state.username for entry in entries]

        assert len(entries) == 1
        assert usernames == ['tester1']

    def test_journaling(self):
        journal = locality.wrap_journal(self.es_client)

        entries = [
            # A user named "t1" who travelled from Toronto to Berlin over the
            # weekend.
            locality.Entry('testingid1', locality.State('locality', 't1', [
                locality.Locality(
                    sourceipaddress='1.2.3.4',
                    city='Toronto',
                    country='CA',
                    lastaction=datetime.utcnow() - timedelta(days=3),
                    latitude=43.6529,
                    longitude=-79.3849,
                    radius=50),
                locality.Locality(
                    sourceipaddress='32.64.128.255',
                    city='Berlin',
                    country='DE',
                    lastaction=datetime.utcnow() - timedelta(minutes=30),
                    latitude=52.520008,
                    longitude=13.404954,
                    radius=50)
            ])),
            # A user named "t2" who only works out of London, UK.
            locality.Entry('testingid2', locality.State('locality', 't2', [
                locality.Locality(
                    sourceipaddress='4.3.2.1',
                    city='London',
                    country='GB',
                    lastaction=datetime.utcnow() - timedelta(minutes=13),
                    latitude=51.509865,
                    longitude=-0.118092,
                    radius=50)
            ]))
        ]

        journal(entries, self.event_index_name)
        
        self.refresh(self.event_index_name)

        query_iface = query.wrap(self.es_client)
        loc_cfg = config.Localities(self.event_index_name, 30, 50.0)

        retrieved = locality.find_all(query_iface, loc_cfg)
        usernames = [entry.state.username for entry in retrieved]

        assert sorted(usernames) == ['t1', 't2']

class TestLocalityIntegrations(unittest.TestCase):
    '''Integration tests for locality functionality.
    '''

    def test_locality_state_update(self):
        loc_query = query_interface([
            {
                '_id': 'identifier1',
                '_source': {
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
            }
        ])
        loc_cfg = config.Localities('localities', 30, 50.0)

        evt_query = query_interface([
            {
                '_source': {
                    'category': 'test',
                    'sourceipaddress': '4.3.2.1',
                    'utctimestamp': '2019-07-31T17:56:38.908000+00:00',
                    'details': {
                        'username': 'tester1'
                    },
                    'sourceipgeolocation': {
                        'city': 'San Francisco',
                        'country_code': 'US',
                        'latitude': 37.773972,
                        'longitude': -122.431297
                    }
                }
            },
            {
                '_source': {
                    'category': 'test',
                    'sourceipaddress': '1.2.4.8',
                    'utctimestamp': '2019-07-31T17:56:38.908000+00:00',
                    'details': {
                        'username': 'tester2'
                    },
                    'sourceipgeolocation': {
                        'city': 'San Francisco',
                        'country_code': 'US',
                        'latitude': 37.773972,
                        'longitude': -122.431297
                    }
                }
            }
        ])
        evt_cfg = config.Events('events', config.SearchWindow(minutes=30), [
            config.QuerySpec(
                lucene='category: test',
                username='_source.details.username')
        ])

        entries = locality.find_all(loc_query, loc_cfg)
        persisted = [entry.state for entry in entries]

        event_sourced = []
        for result in event.find_all(evt_query, evt_cfg):
            loc = event.extract_locality(result.event)

            if loc is not None:
                event_sourced.append(
                    locality.State('locality', result.username, [loc]))

        updates = locality.merge(persisted, event_sourced)

        assert len(updates) == 2
        assert updates[0].did_update and updates[1].did_update
       
        t1 = [u.state for u in updates if u.state.username == 'tester1'][0]
        cities = sorted([loc.city for loc in t1.localities])

        assert cities == ['San Francisco', 'Toronto']

class TestLocality(unittest.TestCase):
    '''unit tests for the `locality` module.
    '''

    def test_find_all_retrieves_all_states(self):
        query_iface = query_interface([
            {
                '_id': 'id1',
                '_source': {
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
            },
            {
                '_id': 'id2',
                '_source': {
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
            }
        ])
        loc_cfg = config.Localities('localities', 30, 50.0)

        entries = locality.find_all(query_iface, loc_cfg)
        usernames = [entry.state.username for entry in entries]
        identifiers = [entry.identifier for entry in entries]

        assert sorted(identifiers) == ['id1', 'id2']
        assert len(entries) == 2
        assert 'tester1' in usernames
        assert 'tester2' in usernames
        assert len(entries[0].state.localities) == 1
        assert len(entries[1].state.localities) == 1

    def test_find_all_ignores_invalid_data(self):
        query_iface = query_interface([
            # Invalid top-level State
            {
                '_id': 'id1',
                '_source': {
                    'type__': 'locality',  # Should have only one underscore (_)
                    'username': 'tester',
                    'localities': []
                }
            },
            # Valid State
            {
                '_id': 'id2',
                '_source': {
                    'type_': 'locality',
                    'username': 'validtester',
                    'localities': []
                }
            },
            # Invalid locality data
            {
                '_id': 'id3',
                '_source': {
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
            }
        ])
        loc_cfg = config.Localities('localities', 30, 50.0)

        entries = locality.find_all(query_iface, loc_cfg)
        usernames = [entry.state.username for entry in entries]

        assert len(entries) == 1
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
        assert last_action > hour_ago

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

    def test_remove_outdated_removes_old_localities(self):
        test_localities = [
            locality.Locality(
                sourceipaddress='32.64.128.255',
                city='Berlin',
                country='DE',
                lastaction=datetime.utcnow() - timedelta(days=10),
                latitude=52.520008,
                longitude=13.404954,
                radius=50),
            locality.Locality(
                sourceipaddress='1.2.3.4',
                city='Toronto',
                country='CA',
                lastaction=datetime.utcnow() - timedelta(days=3),
                latitude=43.6529,
                longitude=-79.3849,
                radius=50)
        ]

        new_localities = locality.remove_outdated(test_localities, 5)

        assert len(test_localities) == 2
        assert len(new_localities) == 1
        assert new_localities[0].city == 'Toronto'
