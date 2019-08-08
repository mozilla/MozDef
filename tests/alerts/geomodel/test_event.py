from datetime import datetime
import pytz
import unittest

import alerts.geomodel.config as config
import alerts.geomodel.event as event
import alerts.geomodel.query as query

from tests.alerts.geomodel.util import query_interface
from tests.unit_test_suite import UnitTestSuite


class TestEventElasticSearch(UnitTestSuite):
    '''Tests for the `event` module that interact with ES.
    '''

    def test_simple_query(self):
        events = [
            {
                'category': 'geomodel',
                'details': {
                    'username': 'testuser1'
                }
            },
            {
                'category': 'geomodel',
                'details': {
                    'username': 'tester2'
                }
            }
        ]

        for evt in events:
            self.populate_test_event(evt)

        self.refresh(self.event_index_name)

        query_iface = query.wrap(self.es_client)
        evt_cfg = config.Events(
            self.event_index_name,
            config.SearchWindow(minutes=30),
            [
                config.QuerySpec(
                    lucene='category: geomodel',
                    username='_source.details.username')
            ])

        results = event.find_all(query_iface, evt_cfg)
        usernames = [result.username for result in results]

        assert len(results) == 2
        assert 'testuser1' in usernames
        assert 'tester2' in usernames


class TestEvent(unittest.TestCase):
    '''Unit tests for the `event` module.
    '''

    def test_find_all_retrieves_usernames(self):
        query_iface = query_interface([
            {
                '_source': {
                    'details': {
                        'username': 'testuser'
                    }
                }
            },
            {
                '_source': {
                    'details': {
                        'username': 'test2'
                    }
                }
            }
        ])
        evt_cfg = config.Events(
            'test_index',
            config.SearchWindow(minutes=30),
            [
                config.QuerySpec(
                    lucene='test',
                    username='_source.details.username')
            ])

        results = event.find_all(query_iface, evt_cfg)
        usernames = [result.username for result in results]

        assert 'testuser' in usernames
        assert 'test2' in usernames

    def test_find_all_handles_bad_username_spec(self):
        query_iface = query_interface([
            {
                '_source': {
                    'details': {
                        'username': 'testuser'
                    }
                }
            },
            {
                '_source': {
                    'details': {
                        'username': 'test2'
                    }
                }
            }
        ])
        evt_cfg = config.Events(
            'test_index',
            config.SearchWindow(minutes=30),
            [
                config.QuerySpec(
                    lucene='test',
                    username='_source.details.nottheusername')  # Wrong key
            ])

        results = event.find_all(query_iface, evt_cfg)
        usernames = [result.username for result in results]

        assert usernames == [None, None]

    def test_find_all_makes_all_requests(self):
        query_iface = query_interface([
            {
                '_source': {
                    'details': {
                        'username': 'testuser'
                    }
                }
            },
            {
                '_source': {
                    'details': {
                        'username': 'test2'
                    }
                }
            }
        ])
        evt_cfg = config.Events(
            'test_index',
            config.SearchWindow(minutes=30),
            [
                config.QuerySpec(
                    lucene='test',
                    username='_source.details.username'),
                config.QuerySpec(
                    lucene='another',
                    username='_source.details.nottheusername')
            ])

        results = event.find_all(query_iface, evt_cfg)
        usernames = [result.username for result in results]

        assert len(results) == 4
        assert None in usernames
        assert 'testuser' in usernames
        assert 'test2' in usernames

    def test_extract_locality_with_missing_data(self):
        bad_events = [
            {
                '__source': 'invalid'
            },
            {
                '_source': {
                    'nottheipaddress': 'somethingelse'
                }
            },
            {
                '_source': {
                    'sourceipaddress': '1.2.3.4',
                    'notthegeolocation': 'uhoh'
                }
            }
        ]

        localities = [event.extract_locality(evt) for evt in bad_events]

        assert all([loc is None for loc in localities])

    def test_extract_locality_provides_default_timestamp(self):
        # Missing `utctimestamp`.
        test_event = {
            '_source': {
                'sourceipaddress': '1.2.3.4',
                'sourceipgeolocation': {
                    'city': 'Toronto',
                    'country_code': 'CA',
                    'latitude': 43.6529,
                    'longitude': -79.3849
                }
            }
        }

        loc = event.extract_locality(test_event)

        assert loc.lastaction < datetime.utcnow().replace(tzinfo=pytz.UTC)

    def test_extract_locality_parses_valid_timestamp(self):
        test_event = {
            '_source': {
                'sourceipaddress': '1.2.3.4',
                'utctimestamp': '2019-07-31T17:56:38.908000+00:00',
                'sourceipgeolocation': {
                    'city': 'Toronto',
                    'country_code': 'CA',
                    'latitude': 43.6529,
                    'longitude': -79.3849
                }
            }
        }

        loc = event.extract_locality(test_event)

        assert loc.sourceipaddress == '1.2.3.4'
        assert loc.lastaction.day == 31
