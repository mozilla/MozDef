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
                    username='details.username')
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
                'details': {
                    'username': 'testuser'
                }
            },
            {
                'details': {
                    'username': 'test2'
                }
            }
        ])
        evt_cfg = config.Events(
            'test_index',
            config.SearchWindow(minutes=30),
            [
                config.QuerySpec(
                    lucene='test',
                    username='details.username')
            ])

        results = event.find_all(query_iface, evt_cfg)
        usernames = [result.username for result in results]

        assert 'testuser' in usernames
        assert 'test2' in usernames

    def test_find_all_handles_bad_username_spec(self):
        query_iface = query_interface([
            {
                'details': {
                    'username': 'testuser'
                }
            },
            {
                'details': {
                    'username': 'test2'
                }
            }
        ])
        evt_cfg = config.Events(
            'test_index',
            config.SearchWindow(minutes=30),
            [
                config.QuerySpec(
                    lucene='test',
                    username='details.nottheusername')  # Wrong key
            ])

        results = event.find_all(query_iface, evt_cfg)
        usernames = [result.username for result in results]

        assert usernames == [None, None]

    def test_find_all_makes_all_requests(self):
        query_iface = query_interface([
            {
                'details': {
                    'username': 'testuser'
                }
            },
            {
                'details': {
                    'username': 'test2'
                }
            }
        ])
        evt_cfg = config.Events(
            'test_index',
            config.SearchWindow(minutes=30),
            [
                config.QuerySpec(
                    lucene='test',
                    username='details.username'),
                config.QuerySpec(
                    lucene='another',
                    username='details.nottheusername')
            ])

        results = event.find_all(query_iface, evt_cfg)
        usernames = [result.username for result in results]

        assert len(results) == 4
        assert None in usernames
        assert 'testuser' in usernames
        assert 'test2' in usernames

    def test_extract_sourceip_recurses_into_dicts(self):
        test_data = {
            'top': {
                'inner1': {
                    'nothere': 'value'
                },
                'inner2': [1, 2, 3, 4],
                'inner3': {
                    'deep': {
                        'sourceipaddress': '4.3.2.1'
                    }
                }
            }
        }

        ip = event.extract_sourceip(test_data)
        assert ip == '4.3.2.1'

    def test_extract_sourceip_recurses_into_lists(self):
        test_data = {
            'top': {
                'dummy': {
                    'key': 'value'
                },
                'dummy2': [1, 2, 3, 4],
                'inner1': [
                    {
                        'sourceipaddress': '1.2.3.4'
                    },
                    {
                        'nottherightkey': 'anothervalue'
                    }
                ]
            }
        }

        ip = event.extract_sourceip(test_data)
        assert ip == '1.2.3.4'
