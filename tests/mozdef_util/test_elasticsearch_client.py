#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# Copyright (c) 2017 Mozilla Corporation

from datetime import datetime, timedelta
import json
import time

import pytest

from mozdef_util.query_models import SearchQuery, TermMatch, Aggregation, ExistsMatch
from mozdef_util.elasticsearch_client import ElasticsearchClient, ElasticsearchInvalidIndex, DOCUMENT_TYPE

from tests.unit_test_suite import UnitTestSuite


class ElasticsearchClientTest(UnitTestSuite):
    def setup(self):
        super().setup()
        self.es_client = ElasticsearchClient(self.options.esservers, bulk_refresh_time=3)

    def get_num_events(self):
        self.refresh('events')
        search_query = SearchQuery()
        search_query.add_must(TermMatch('_type', DOCUMENT_TYPE))
        search_query.add_aggregation(Aggregation('_type'))
        results = search_query.execute(self.es_client)
        if len(results['aggregations']['_type']['terms']) != 0:
            return results['aggregations']['_type']['terms'][0]['count']
        else:
            return 0


class MockTransportClass:

    def __init__(self):
        self.request_counts = 0
        self.original_function = None

    def backup_function(self, orig_function):
        self.original_function = orig_function

    def perform_request(self, method, url, headers=None, params=None, body=None):
        if url == '/_bulk' or url == '/events/_doc':
            self.request_counts += 1
        return self.original_function(method, url, params=params, body=body)


class TestWriteWithRead(ElasticsearchClientTest):
    def setup(self):
        super().setup()

        self.alert = {
            'category': 'correlatedalerts',
            'events': [
                {
                    'documentid': 'l-a3V5mbQl-C91RDzjpNig',
                    'documentindex': 'events-20160819',
                    'documentsource': {
                        'category': 'bronotice',
                        'details': {
                            'hostname': 'testhostname',
                            'note': 'CrowdStrike::Correlated_Alerts example alert',
                            'sourceipaddress': '1.2.3.4'
                        },
                        'eventsource': 'nsm',
                        'hostname': 'nsm',
                        'processid': '1337',
                        'processname': 'syslog',
                        'receivedtimestamp': '2016-08-19T16:40:55.818595+00:00',
                        'severity': 'NOTICE',
                        'source': 'nsm_src',
                        'summary': 'CrowdStrike::Correlated_Alerts Host 1.2.3.4 caused an alert to throw',
                        'tags': ['tag1', 'tag2'],
                        'timestamp': '2016-08-19T16:40:55.818595+00:00',
                        'utctimestamp': '2016-08-19T16:40:55.818595+00:00'
                    },
                }
            ],
            'severity': 'NOTICE',
            'summary': 'nsm CrowdStrike::Correlated_Alerts Host 1.2.3.4 caused an alert to throw',
            'tags': [
                'nsm',
                'bro',
                'correlated'
            ],
            'url': 'https://mozilla.org',
            'utctimestamp': '2016-08-19T16:40:57.851092+00:00'
        }
        self.saved_alert = self.es_client.save_alert(body=self.alert)
        self.refresh('alerts')

    def test_saved_index(self):
        assert self.saved_alert['_index'] == self.alert_index_name

    def test_alert_source(self):
        self.fetched_alert = self.es_client.get_alert_by_id(self.saved_alert['_id'])
        assert self.fetched_alert['_source'] == self.alert

    def test_bad_id(self):
        assert self.es_client.get_alert_by_id("123") is None


class TestNoResultsFound(ElasticsearchClientTest):

    def test_search_no_results(self):
        search_query = SearchQuery()
        search_query.add_must(TermMatch('garbagefielddoesntexist', 'testingvalues'))
        results = search_query.execute(self.es_client)
        assert results['hits'] == []


class TestCloseIndex(ElasticsearchClientTest):

    def teardown(self):
        super().teardown()
        if self.config_delete_indexes:
            self.es_client.delete_index('test_index')

    def test_close_index(self):
        if not self.es_client.index_exists('test_index'):
            self.es_client.create_index('test_index')
        time.sleep(1)
        closed = self.es_client.close_index('test_index')
        assert closed == {'acknowledged': True}


class TestWritingToClosedIndex(ElasticsearchClientTest):

    def teardown(self):
        super().teardown()
        if self.config_delete_indexes:
            self.es_client.delete_index('test_index')

    def test_writing_to_closed_index(self):
        if not self.es_client.index_exists('test_index'):
            self.es_client.create_index('test_index')
        time.sleep(1)
        self.es_client.close_index('test_index')
        event = json.dumps({"key": "example value for string of json test"})
        with pytest.raises(Exception):
            self.es_client.save_event(index='test_index', body=event)


class TestOpenIndex(ElasticsearchClientTest):

    def teardown(self):
        super().teardown()
        if self.config_delete_indexes:
            self.es_client.delete_index('test_index')

    def test_index_open(self):
        if not self.es_client.index_exists('test_index'):
            self.es_client.create_index('test_index')
        time.sleep(1)
        self.es_client.close_index('test_index')
        opened = self.es_client.open_index('test_index')
        assert opened == {'acknowledged': True, 'shards_acknowledged': True}


class TestWithBadIndex(ElasticsearchClientTest):

    def test_search_nonexisting_index(self):
        search_query = SearchQuery()
        search_query.add_must(TermMatch('key', 'value'))
        with pytest.raises(ElasticsearchInvalidIndex):
            search_query.execute(self.es_client, indices=['doesnotexist'])


class TestSimpleWrites(ElasticsearchClientTest):

    def test_simple_writing_event_dict(self):
        mock_class = MockTransportClass()
        mock_class.backup_function(self.es_client.es_connection.transport.perform_request)
        self.es_client.es_connection.transport.perform_request = mock_class.perform_request

        event_length = 100
        events = []
        for num in range(event_length):
            events.append({"key": "value" + str(num)})

        for event in events:
            self.es_client.save_event(body=event)

        assert mock_class.request_counts == 100
        self.refresh(self.event_index_name)
        num_events = self.get_num_events()
        assert num_events == 100

    def test_simple_writing_event_string(self):
        event = json.dumps({"key": "example value for string of json test"})
        self.es_client.save_event(body=event)

        self.refresh(self.event_index_name)
        num_events = self.get_num_events()
        assert num_events == 1

        query = SearchQuery()
        query.add_must(ExistsMatch('key'))
        results = query.execute(self.es_client)
        assert sorted(results['hits'][0].keys()) == ['_id', '_index', '_score', '_source']
        assert results['hits'][0]['_source']['key'] == 'example value for string of json test'

        assert len(results['hits']) == 1
        assert results['hits'][0]['_source']['type'] == 'event'

    def test_writing_dot_fieldname(self):
        event = json.dumps({"key.othername": "example value for string of json test"})
        self.es_client.save_event(body=event)

        self.refresh(self.event_index_name)
        num_events = self.get_num_events()
        assert num_events == 1

        query = SearchQuery()
        query.add_must(ExistsMatch('key.othername'))
        results = query.execute(self.es_client)
        assert sorted(results['hits'][0].keys()) == ['_id', '_index', '_score', '_source']
        assert results['hits'][0]['_source']['key.othername'] == 'example value for string of json test'

        assert len(results['hits']) == 1

    def test_writing_event_defaults(self):
        query = SearchQuery()
        default_event = {}
        self.populate_test_event(default_event)
        self.refresh(self.event_index_name)

        query.add_must(ExistsMatch('summary'))
        results = query.execute(self.es_client)
        assert len(results['hits']) == 1
        assert sorted(results['hits'][0].keys()) == ['_id', '_index', '_score', '_source']
        saved_event = results['hits'][0]['_source']
        assert 'category' in saved_event
        assert 'details' in saved_event
        assert 'hostname' in saved_event
        assert 'mozdefhostname' in saved_event
        assert 'processid' in saved_event
        assert 'processname' in saved_event
        assert 'receivedtimestamp' in saved_event
        assert 'severity' in saved_event
        assert 'source' in saved_event
        assert 'summary' in saved_event
        assert 'tags' in saved_event
        assert 'timestamp' in saved_event
        assert 'utctimestamp' in saved_event
        assert 'category' in saved_event

    def test_writing_with_details(self):
        query = SearchQuery()
        default_event = {
            "_source": {
                "receivedtimestamp": UnitTestSuite.current_timestamp(),
                "summary": "Test summary",
                "details": {
                    "note": "Example note",
                }
            }
        }
        self.populate_test_event(default_event)
        self.refresh(self.event_index_name)

        query.add_must(ExistsMatch('summary'))
        results = query.execute(self.es_client)
        assert len(results['hits']) == 1
        assert sorted(results['hits'][0].keys()) == ['_id', '_index', '_score', '_source']
        assert results['hits'][0]['_source']['summary'] == 'Test summary'
        assert results['hits'][0]['_source']['details'] == {"note": "Example note"}

    def test_writing_with_source(self):
        query = SearchQuery()
        default_event = {
            "_source": {
                "receivedtimestamp": UnitTestSuite.current_timestamp(),
                "summary": "Test summary",
                "details": {
                    "note": "Example note",
                }
            }
        }
        self.populate_test_event(default_event)
        self.refresh(self.event_index_name)

        query.add_must(ExistsMatch('summary'))
        results = query.execute(self.es_client)
        assert len(results['hits']) == 1
        assert sorted(results['hits'][0].keys()) == ['_id', '_index', '_score', '_source']


class BulkTest(ElasticsearchClientTest):

    def setup(self):
        super().setup()
        self.mock_class = MockTransportClass()
        self.mock_class.backup_function(self.es_client.es_connection.transport.perform_request)
        self.es_client.es_connection.transport.perform_request = self.mock_class.perform_request

    def teardown(self):
        self.es_client.finish_bulk()
        super().teardown()


class TestBulkWrites(BulkTest):

    def test_bulk_writing_simple(self):
        event_length = 2000
        events = []
        for num in range(event_length):
            events.append({"key": "value" + str(num)})

        assert self.mock_class.request_counts == 0
        for event in events:
            self.es_client.save_event(body=event, bulk=True)

        self.refresh(self.event_index_name)
        time.sleep(1)

        # We encountered a weird bug in travis
        # that would sometimes cause the number
        # of requests sent to ES to fluctuate.
        # As a result, we're checking within 5 requests
        # from 20, to verify we are still using bulk
        assert self.mock_class.request_counts <= 25 and self.mock_class.request_counts >= 15
        num_events = self.get_num_events()
        assert num_events == 2000


class TestBulkWritesWithMoreThanThreshold(BulkTest):

    def test_bulk_writing_more_threshold(self):
        event_length = 1995
        events = []
        for num in range(event_length):
            events.append({"key": "value" + str(num)})

        for event in events:
            self.es_client.save_object(index='events', body=event, bulk=True)

        self.refresh(self.event_index_name)

        # We encountered a weird bug in travis
        # that would sometimes cause the number
        # of requests sent to ES to fluctuate.
        # As a result, we're checking within 5 requests
        # from 20, to verify we are still using bulk
        non_refreshed_request_count = self.mock_class.request_counts
        assert self.mock_class.request_counts <= 25 and self.mock_class.request_counts >= 15
        assert self.get_num_events() == 1900
        time.sleep(5)
        # All we want to check here is that during the sleep
        # we purged the queue and sent the remaining events to ES
        assert self.mock_class.request_counts > non_refreshed_request_count
        self.refresh(self.event_index_name)
        assert self.get_num_events() == 1995


class TestBulkWritesWithLessThanThreshold(BulkTest):

    def test_bulk_writing_less_threshold(self):
        self.es_client.save_event(body={'key': 'value'}, bulk=True)
        assert self.get_num_events() == 0
        assert self.mock_class.request_counts == 0

        event_length = 5
        for num in range(event_length):
            self.es_client.save_event(body={"key": "value" + str(num)}, bulk=True)

        assert self.get_num_events() == 0

        self.refresh(self.event_index_name)
        time.sleep(5)
        assert self.get_num_events() == 6


class TestWriteWithID(ElasticsearchClientTest):

    def test_write_with_id(self):
        event = {'key': 'value'}
        saved_event = self.es_client.save_event(body=event, doc_id="12345")
        assert saved_event['_id'] == '12345'


class TestWriteWithIDExists(ElasticsearchClientTest):

    def test_write_with_id(self):
        event_id = "12345"
        event = {'key': 'value'}
        saved_event = self.es_client.save_event(body=event, doc_id=event_id)
        assert saved_event['_id'] == event_id
        event['new_key'] = 'updated_value'
        saved_event = self.es_client.save_event(body=event, doc_id=event_id)
        assert saved_event['_id'] == event_id
        self.refresh(self.event_index_name)
        self.es_client.get_event_by_id(event_id)


class TestGetIndices(ElasticsearchClientTest):

    def teardown(self):
        super().teardown()
        if self.config_delete_indexes:
            self.es_client.delete_index('test_index')

    def test_get_indices(self):
        if self.config_delete_indexes:
            self.es_client.create_index('test_index')
        time.sleep(1)
        all_indices = self.es_client.get_indices()
        all_indices.sort()
        open_indices = self.es_client.get_open_indices()
        open_indices.sort()
        expected_indices = [self.alert_index_name, self.previous_event_index_name, self.event_index_name, 'test_index']

        # Either both of all_indices and open_indices are the same as
        # expected_indices OR both of the former sets contain an additional
        # index in case the day changed while testing.
        current_name = self.event_index_name.split('-')[1]  # eg events-20200312
        current_day = datetime(
            int(current_name[0:4]),  # Year
            int(current_name[4:6]),  # Month
            int(current_name[6:8]),  # Day
        )
        next_day = current_day + timedelta(days=1)
        next_name = "{}{}{}".format(
            next_day.year, next_day.month, next_day.day
        )

        next_index_name = "events-{}".format(next_name)

        assert all([expected in all_indices for expected in expected_indices])
        assert all([expected in open_indices for expected in expected_indices])
        assert ((len(expected_indices) == len(all_indices)) or
                (len(expected_indices) + 1 == len(all_indices) and
                 next_index_name in all_indices))
        assert ((len(expected_indices) == len(open_indices)) or
                (len(expected_indices) + 1 == len(open_indices) and
                 next_index_name in open_indices))

    def test_closed_get_indices(self):
        if self.config_delete_indexes:
            self.es_client.create_index('test_index')
        time.sleep(1)
        self.es_client.close_index('test_index')
        all_indices = self.es_client.get_indices()
        open_indices = self.es_client.get_open_indices()
        assert 'test_index' in all_indices
        assert 'test_index' not in open_indices


class TestIndexExists(ElasticsearchClientTest):

    def teardown(self):
        super().teardown()
        if self.config_delete_indexes:
            self.es_client.delete_index('test_index')

    def test_index_exists(self):
        if self.config_delete_indexes:
            self.es_client.create_index('test_index')
        time.sleep(1)
        indices = self.es_client.index_exists('test_index')
        assert indices is True


class TestClusterHealth(ElasticsearchClientTest):

    def test_cluster_health_results(self):
        health_results = self.es_client.get_cluster_health()
        health_keys = sorted(health_results.keys())
        assert health_keys == ['active_primary_shards', 'active_shards', 'cluster_name', 'initializing_shards', 'number_of_data_nodes', 'number_of_nodes', 'relocating_shards', 'status', 'timed_out', 'unassigned_shards']
        assert type(health_results['active_primary_shards']) is int
        assert type(health_results['active_shards']) is int
        assert type(health_results['cluster_name']) is str
        assert type(health_results['initializing_shards']) is int
        assert type(health_results['number_of_data_nodes']) is int
        assert type(health_results['number_of_nodes']) is int
        assert type(health_results['relocating_shards']) is int
        assert type(health_results['status']) is str
        assert type(health_results['timed_out']) is bool
        assert type(health_results['unassigned_shards']) is int


class TestCreatingAlias(ElasticsearchClientTest):

    def setup(self):
        super().setup()
        if self.config_delete_indexes:
            self.es_client.delete_index('index1', True)
            self.es_client.delete_index('index2', True)
            self.es_client.delete_index('alias1', True)

    def teardown(self):
        super().teardown()
        if self.config_delete_indexes:
            self.es_client.delete_index('index1', True)
            self.es_client.delete_index('index2', True)
            self.es_client.delete_index('alias1', True)

    def test_simple_create_alias(self):
        if self.config_delete_indexes:
            self.es_client.create_index('index1')
            self.es_client.create_alias('alias1', 'index1')
        alias_indices = self.es_client.get_alias('alias1')
        assert alias_indices == ['index1']
        indices = self.es_client.get_indices()
        assert 'index1' in indices

    def test_alias_multiple_indices(self):
        if self.config_delete_indexes:
            self.es_client.create_index('index1')
            self.es_client.create_index('index2')
            self.es_client.create_alias('alias1', 'index1')
            self.es_client.create_alias('alias1', 'index2')
        alias_indices = self.es_client.get_alias('alias1')
        assert alias_indices == ['index2']
        indices = self.es_client.get_indices()
        assert 'index1' in indices
        assert 'index2' in indices

    def test_create_alias_multiple_indices(self):
        self.es_client.create_index('index1')
        self.es_client.create_index('index2')
        self.es_client.create_alias_multiple_indices('alias1', ['index1', 'index2'])
        alias_indices = self.es_client.get_alias('alias1')
        assert len(alias_indices) == 2
        assert 'index1' in alias_indices
        assert 'index2' in alias_indices
        indices = self.es_client.get_indices()
        assert 'index1' in indices
        assert 'index2' in indices


class TestBulkInvalidFormatProblem(BulkTest):

    def setup(self):
        super().setup()

        mapping = {
            "mappings": {
                DOCUMENT_TYPE: {
                    "properties": {
                        "utcstamp": {
                            "type": "date",
                            "format": "dateOptionalTime"
                        }
                    }
                }
            }
        }

        # Recreate the test indexes with a custom mapping to throw
        # parsing errors
        if self.config_delete_indexes:
            self.es_client.delete_index("events", True)
            self.es_client.delete_index(self.event_index_name, True)
            self.es_client.create_index(self.event_index_name, index_config=mapping)
            self.es_client.create_alias('events', self.event_index_name)
            self.es_client.create_alias('events-previous', self.event_index_name)

    def test_bulk_problems(self):
        event = {
            "utcstamp": "2016-11-08T14:13:01.250631+00:00"
        }
        malformed_event = {
            "utcstamp": "abc",
        }

        self.es_client.save_object(index='events', body=event, bulk=True)
        self.es_client.save_object(index='events', body=malformed_event, bulk=True)
        self.refresh(self.event_index_name)
        time.sleep(5)
        assert self.get_num_events() == 1
