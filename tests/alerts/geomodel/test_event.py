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
            'category: geomodel',
            '_source.details.username')

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
            'test',
            '_source.details.username')

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
            'test',
            '_source.details.nottheusername')  # Wrong key

        results = event.find_all(query_iface, evt_cfg)
        usernames = [result.username for result in results]

        assert usernames == [None, None]
