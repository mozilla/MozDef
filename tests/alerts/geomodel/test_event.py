import unittest

import alerts.geomodel.config as config
import alerts.geomodel.event as event

from tests.alerts.geomodel.util import query_interface


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
