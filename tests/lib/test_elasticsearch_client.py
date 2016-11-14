import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), "../../lib"))
from query_models import SearchQuery, TermMatch, Aggregation

sys.path.append(os.path.join(os.path.dirname(__file__), "../../alerts/lib"))
from config import ES

sys.path.append(os.path.join(os.path.dirname(__file__), "../"))
from unit_test_suite import UnitTestSuite

import time

from elasticsearch_client import ElasticsearchClient, ElasticsearchInvalidIndex
import pytest

# Remove this code when pyes is gone!
import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), "../../lib"))
import pyes_enabled
# Remove this code when pyes is gone!


class ElasticsearchClientTest(UnitTestSuite):
    def setup(self):
        super(ElasticsearchClientTest, self).setup()
        self.es_client = ElasticsearchClient(ES['servers'], bulk_refresh_time=3)

    def get_num_events(self):
        self.es_client.flush('events')
        search_query = SearchQuery()
        search_query.add_must(TermMatch('_type', 'event'))
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
        # Exclude certain paths/urls so that we only
        # count requests that were made to ADD events
        self.exclude_paths = [
            "/events,events-previous/_search",
            "/events/_flush",
            "/_all/_flush",
            "/events%2Cevents-previous/_search"
        ]

    def _send_request(self, method, path, body=None, params=None, headers=None, raw=False, return_response=False):
        if path not in self.exclude_paths:
            self.request_counts += 1
        return self.original_function(method, path, body, params)

    def backup_function(self, orig_function):
        self.original_function = orig_function

    def perform_request(self, method, url, params=None, body=None, timeout=None, ignore=()):
        if url not in self.exclude_paths:
            self.request_counts += 1
        return self.original_function(method, url, params=params, body=body)


class TestWriteWithRead(ElasticsearchClientTest):
    def setup(self):
        super(TestWriteWithRead, self).setup()

        self.alert = {'category': 'correlatedalerts',
                 'events': [{'documentid': 'l-a3V5mbQl-C91RDzjpNig',
                             'documentindex': 'events-20160819',
                             'documentsource': {'category': 'bronotice',
                                                'details': {'hostname': 'testhostname',
                                                            'note': 'CrowdStrike::Correlated_Alerts example alert',
                                                            'sourceipaddress': '1.2.3.4'},
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
                                                'utctimestamp': '2016-08-19T16:40:55.818595+00:00'},
                             'documenttype': 'bro'}],
                 'severity': 'NOTICE',
                 'summary': 'nsm CrowdStrike::Correlated_Alerts Host 1.2.3.4 caused an alert to throw',
                 'tags': ['nsm,bro,correlated'],
                 'url': 'https://mana.mozilla.org/wiki/display/SECURITY/NSM+IR+procedures',
                 'utctimestamp': '2016-08-19T16:40:57.851092+00:00'}
        self.saved_alert = self.es_client.save_alert(body=self.alert)
        self.es_client.flush('alerts')

    def test_saved_type(self):
        assert self.saved_alert['_type'] == 'alert'

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


class TestWithBadIndex(ElasticsearchClientTest):

    def test_search_nonexisting_index(self):
        search_query = SearchQuery()
        search_query.add_must(TermMatch('key', 'value'))
        with pytest.raises(ElasticsearchInvalidIndex):
            search_query.execute(self.es_client, indices=['doesnotexist'])


class TestSimpleWrites(ElasticsearchClientTest):

    def test_simple_writing(self):
        mock_class = MockTransportClass()

        if pyes_enabled.pyes_on is True:
            mock_class.backup_function(self.es_client.es_connection._send_request)
            self.es_client.es_connection._send_request = mock_class._send_request
        else:
            mock_class.backup_function(self.es_client.es_connection.transport.perform_request)
            self.es_client.es_connection.transport.perform_request = mock_class.perform_request

        event_length = 10000
        events = []
        for num in range(event_length):
            events.append({"key": "value" + str(num)})

        for event in events:
            self.es_client.save_event(body=event)
        self.es_client.flush('events')

        assert mock_class.request_counts == 10000
        num_events = self.get_num_events()
        assert num_events == 10000


class BulkTest(ElasticsearchClientTest):

    def setup(self):
        super(BulkTest, self).setup()
        self.mock_class = MockTransportClass()

        if pyes_enabled.pyes_on is True:
            self.mock_class.backup_function(self.es_client.es_connection._send_request)
            self.es_client.es_connection._send_request = self.mock_class._send_request
        else:
            self.mock_class.backup_function(self.es_client.es_connection.transport.perform_request)
            self.es_client.es_connection.transport.perform_request = self.mock_class.perform_request

    def teardown(self):
        super(BulkTest, self).teardown()
        self.es_client.finish_bulk()


class TestBulkWrites(BulkTest):

    def test_bulk_writing(self):
        event_length = 10000
        events = []
        for num in range(event_length):
            events.append({"key": "value" + str(num)})

        assert self.mock_class.request_counts == 0
        for event in events:
            self.es_client.save_event(body=event, bulk=True)
        self.es_client.flush('events')

        assert self.mock_class.request_counts == 100
        num_events = self.get_num_events()
        assert num_events == 10000


class TestBulkWritesWithMoreThanThreshold(BulkTest):

    def test_bulk_writing(self):
        event_length = 9995
        events = []
        for num in range(event_length):
            events.append({"key": "value" + str(num)})

        for event in events:
            self.es_client.save_object(index='events', doc_type='event', body=event, bulk=True)
        self.es_client.flush('events')

        assert self.mock_class.request_counts == 99
        assert self.get_num_events() == 9900
        time.sleep(3)
        self.es_client.flush('events')
        assert self.mock_class.request_counts == 100
        assert self.get_num_events() == 9995


class TestBulkWritesWithLessThanThreshold(BulkTest):

    def test_bulk_writing(self):
        self.es_client.save_event(body={'key': 'value'}, bulk=True)
        assert self.get_num_events() == 0
        assert self.mock_class.request_counts == 0

        event_length = 5
        for num in range(event_length):
            self.es_client.save_event(body={"key": "value" + str(num)}, bulk=True)

        assert self.get_num_events() == 0
        time.sleep(3)
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
        self.es_client.flush('events')
        fetched_event = self.es_client.get_event_by_id(event_id)
        assert fetched_event['_source'] == event


class TestGetIndices(ElasticsearchClientTest):

    def teardown(self):
        super(TestGetIndices, self).teardown()
        self.es_client.delete_index('test_index')

    def test_get_indices(self):
        self.es_client.create_index('test_index')
        time.sleep(0.5)
        indices = self.es_client.get_indices()
        indices.sort()
        assert indices == [self.alert_index_name, self.event_index_name, 'test_index']


class TestClusterHealth(ElasticsearchClientTest):

    def test_cluster_health_results(self):
        health_results = self.es_client.get_cluster_health()
        health_keys = health_results.keys()
        health_keys.sort()
        assert health_keys == ['active_primary_shards', 'active_shards', 'cluster_name', 'initializing_shards', 'number_of_data_nodes', 'number_of_nodes', 'relocating_shards', 'status', 'timed_out', 'unassigned_shards']
        assert type(health_results['active_primary_shards']) is int
        assert type(health_results['active_shards']) is int
        if pyes_enabled.pyes_on is True:
            assert type(health_results['cluster_name']) is str
        else:
            assert type(health_results['cluster_name']) is unicode
        assert type(health_results['initializing_shards']) is int
        assert type(health_results['number_of_data_nodes']) is int
        assert type(health_results['number_of_nodes']) is int
        assert type(health_results['relocating_shards']) is int
        if pyes_enabled.pyes_on is True:
            assert type(health_results['status']) is str
        else:
            assert type(health_results['status']) is unicode
        assert type(health_results['timed_out']) is bool
        assert type(health_results['unassigned_shards']) is int


class TestCreatingAlias(ElasticsearchClientTest):

    def setup(self):
        super(TestCreatingAlias, self).setup()
        self.es_client.delete_index('index1', True)
        self.es_client.delete_index('index2', True)
        self.es_client.delete_index('alias1', True)

    def teardown(self):
        super(TestCreatingAlias, self).teardown()
        self.es_client.delete_index('index1', True)
        self.es_client.delete_index('index2', True)
        self.es_client.delete_index('alias1', True)

    def test_simple_create_alias(self):
        self.es_client.create_index('index1')
        self.es_client.create_alias('alias1', 'index1')
        alias_indices = self.es_client.get_alias('alias1')
        assert alias_indices == ['index1']
        indices = self.es_client.get_indices()
        assert 'index1' in indices

    def test_alias_multiple_indices(self):
        self.es_client.create_index('index1')
        self.es_client.create_index('index2')
        self.es_client.create_alias('alias1', 'index1')
        self.es_client.create_alias('alias1', 'index2')
        alias_indices = self.es_client.get_alias('alias1')
        assert alias_indices == ['index2']
        indices = self.es_client.get_indices()
        assert 'index1' in indices
        assert 'index2' in indices


if pyes_enabled.pyes_on is not True:
    # Instead of trying to figure out how to update mappings via pyes, I decided
    # to just skip this unit test since we'll be ripping it out soon
    class TestBulkInvalidFormatProblem(BulkTest):

        def setup(self):
            super(TestBulkInvalidFormatProblem, self).setup()

            mapping = {
                "mappings": {
                    "event": {
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
            self.es_client.delete_index("events", True)
            self.es_client.delete_index(self.event_index_name, True)
            self.es_client.create_index(self.event_index_name, mapping=mapping)
            self.es_client.create_alias('events', self.event_index_name)
            self.es_client.create_alias('events-previous', self.event_index_name)

        def test_bulk_problems(self):
            event = {
                "utcstamp": "2016-11-08T14:13:01.250631+00:00"
            }
            malformed_event = {
                "utcstamp": "abc",
            }

            self.es_client.save_object(index='events', doc_type='event', body=event, bulk=True)
            self.es_client.save_object(index='events', doc_type='event', body=malformed_event, bulk=True)
            time.sleep(5)
            assert self.get_num_events() == 1
