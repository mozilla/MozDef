from typing import Any, Dict, List
import unittest

from mozdef_util.query_models import SearchQuery

import mozdef_geomodel.config as config
import mozdef_geomodel.event as event
import mozdef_geomodel.query as query


def _query_interface(results: List[Dict[str, Any]]) -> query.QueryInterface:
    '''Produce a `QueryInterface` that just returns the provided results.
    '''

    def closure(q: SearchQuery, esi: str) -> List[Dict[str, Any]]:
        return results

    return closure


class TestEvent(unittest.TestCase):
    '''Unit tests for the `event` module.
    '''

    def test_find_all_retrieves_usernames(self):
        query_iface = _query_interface([
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
        query_iface = _query_interface([
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
        query_iface = _query_interface([
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

