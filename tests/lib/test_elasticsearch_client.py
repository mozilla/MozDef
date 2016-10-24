import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), "../../lib"))

from query_models import SearchQuery, TermMatch, Aggregation

sys.path.append(os.path.join(os.path.dirname(__file__), "../"))
from unit_test_suite import UnitTestSuite

# Remove this code when pyes is gone!
import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), "../../lib"))
import pyes_enabled
# Remove this code when pyes is gone!


class ElasticsearchClientTest(UnitTestSuite):
    def setup(self):
        super(ElasticsearchClientTest, self).setup()

    def get_num_events(self):
        search_query = SearchQuery()
        search_query.add_must(TermMatch('_type', 'event'))
        search_query.add_aggregation(Aggregation('_type'))
        results = search_query.execute(self.es_client)
        return results['aggregations']['_type']['terms'][0]['count']


class MockTransportClass:

    def __init__(self):
        self.request_counts = 0
        self.original_function = None

    def _send_request(self, method, path, body=None, params=None, headers=None, raw=False, return_response=False):
        self.request_counts += 1
        return self.original_function(method, path, body, params)

    def backup_function(self, orig_function):
        self.original_function = orig_function

    def perform_request(self, method, url, params=None, body=None, timeout=None, ignore=()):
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
        assert self.saved_alert['_index'] == 'alerts'

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

        assert mock_class.request_counts == 10001
        num_events = self.get_num_events()
        assert num_events == 10000


class TestBulkWrites(ElasticsearchClientTest):

    def test_bulk_writing(self):
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
            self.es_client.save_event(body=event, bulk=True)
        self.es_client.flush('events')

        assert mock_class.request_counts == 101
        num_events = self.get_num_events()
        assert num_events == 10000


class TestBulkWritesWithMoreThanThreshold(ElasticsearchClientTest):

    def test_bulk_writing(self):
        mock_class = MockTransportClass()

        if pyes_enabled.pyes_on is True:
            mock_class.backup_function(self.es_client.es_connection._send_request)
            self.es_client.es_connection._send_request = mock_class._send_request
        else:
            mock_class.backup_function(self.es_client.es_connection.transport.perform_request)
            self.es_client.es_connection.transport.perform_request = mock_class.perform_request

        event_length = 9995
        events = []
        for num in range(event_length):
            events.append({"key": "value" + str(num)})

        for event in events:
            self.es_client.save_event(body=event, bulk=True)
        self.es_client.flush('events')

        assert mock_class.request_counts == 101
        num_events = self.get_num_events()
        assert num_events == 9995


class TestBulkWritesWithLessThanThreshold(ElasticsearchClientTest):

    def test_bulk_writing(self):
        self.es_client.save_event(body={'key': 'value'}, bulk=True)
        id_match = TermMatch('_type', 'event')
        search_query = SearchQuery()
        search_query.add_must(id_match)
        results = search_query.execute(self.es_client, indices=['events'])
        assert len(results['hits']) == 0

        event_length = 100
        events = []
        for num in range(event_length):
            events.append({"key": "value" + str(num)})

        for event in events:
            self.es_client.save_event(body=event, bulk=True)
        self.es_client.flush('events')

        id_match = TermMatch('_type', 'event')
        search_query = SearchQuery()
        search_query.add_must(id_match)
        results = search_query.execute(self.es_client, indices=['events'])
        assert len(results['hits']) == 101


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
