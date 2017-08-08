import pytest

from datetime import datetime

import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), "../../../lib"))
from query_models import SearchQuery, ExistsMatch, TermMatch, Aggregation

sys.path.append(os.path.join(os.path.dirname(__file__), "../../"))
from unit_test_suite import UnitTestSuite


class SearchQueryUnitTest(UnitTestSuite):

    def setup(self):
        super(SearchQueryUnitTest, self).setup()
        self.query = SearchQuery()
        assert self.query.must == []
        assert self.query.must_not == []
        assert self.query.should == []
        assert self.query.aggregation == []

    def populate_example_event(self):
        event = {
            'summary': 'Test Summary',
            'note': 'Example note',
            'details': {
                'information': 'Example information'
            }
        }
        self.populate_test_event(event)


class TestMustInput(SearchQueryUnitTest):

    def test_simple_input(self):
        self.query.add_must(ExistsMatch('note'))
        assert self.query.must == [ExistsMatch('note')]

    def test_array_input(self):
        queries = [
            ExistsMatch('note'),
            TermMatch('note', 'test')
        ]
        self.query.add_must(queries)
        assert self.query.must == queries

    def test_populated_array(self):
        self.query.add_must(ExistsMatch('details'))
        self.query.add_must([ExistsMatch('note'), TermMatch('note', 'test')])
        assert self.query.must == [ExistsMatch('details'), ExistsMatch('note'), TermMatch('note', 'test')]


class TestMustNotInput(SearchQueryUnitTest):

    def test_simple_input(self):
        self.query.add_must_not(ExistsMatch('note'))
        assert self.query.must_not == [ExistsMatch('note')]

    def test_array_input(self):
        queries = [
            ExistsMatch('note'),
            TermMatch('note', 'test')
        ]
        self.query.add_must_not(queries)
        assert self.query.must_not == queries

    def test_populated_array(self):
        self.query.add_must_not(ExistsMatch('details'))
        self.query.add_must_not([ExistsMatch('note'), TermMatch('note', 'test')])
        assert self.query.must_not == [ExistsMatch('details'), ExistsMatch('note'), TermMatch('note', 'test')]


class TestShouldInput(SearchQueryUnitTest):

    def test_simple_input(self):
        self.query.add_should(ExistsMatch('note'))
        assert self.query.should == [ExistsMatch('note')]

    def test_array_input(self):
        queries = [
            ExistsMatch('note'),
            TermMatch('note', 'test')
        ]
        self.query.add_should(queries)
        assert self.query.should == queries

    def test_populated_array(self):
        self.query.add_should(ExistsMatch('details'))
        self.query.add_should([ExistsMatch('note'), TermMatch('note', 'test')])
        assert self.query.should == [ExistsMatch('details'), ExistsMatch('note'), TermMatch('note', 'test')]


class TestAggregationInput(SearchQueryUnitTest):

    def test_simple_input(self):
        self.query.add_aggregation(Aggregation('note'))
        assert self.query.aggregation == [Aggregation('note')]

    def test_multiple_values(self):
        self.query.add_aggregation(Aggregation('note'))
        self.query.add_aggregation(Aggregation('summary'))
        assert self.query.aggregation == [Aggregation('note'), Aggregation('summary')]


class TestExecute(SearchQueryUnitTest):

    def test_complex_aggregation_query_execute(self):
        query = SearchQuery()
        assert query.date_timedelta == {}
        query.add_must(ExistsMatch('ip'))
        query.add_aggregation(Aggregation('ip'))
        self.populate_test_event(
            {
                'summary': 'Test Summary',
                'ip': '127.0.0.1',
                'details': {
                    'information': 'Example information'
                }
            }
        )
        self.populate_test_event(
            {
                'summary': 'Test Summary',
                'ip': '1.2.3.4',
                'details': {
                    'information': 'Example information'
                }
            }
        )
        self.populate_test_event(
            {
                'summary': 'Test Summary',
                'ip': '1.2.3.4',
                'details': {
                    'information': 'Example information'
                }
            }
        )

        self.flush(self.event_index_name)

        results = query.execute(self.es_client)
        assert results.keys() == ['hits', 'meta', 'aggregations']
        assert results['meta'].keys() == ['timed_out']
        assert results['meta']['timed_out'] is False

        sorted_hits = sorted(results['hits'], key=lambda k: k['_source']['ip'])

        assert len(sorted_hits) == 3

        assert sorted_hits[0].keys() == ['_score', '_type', '_id', '_source', '_index']
        assert type(sorted_hits[0]['_id']) == unicode
        assert sorted_hits[0]['_type'] == 'event'

        assert sorted_hits[0]['_index'] == datetime.now().strftime("events-%Y%m%d")

        assert sorted_hits[0]['_source'].keys() == ['ip', 'details', 'summary']
        assert sorted_hits[0]['_source']['ip'] == '1.2.3.4'
        assert sorted_hits[0]['_source']['summary'] == 'Test Summary'

        assert sorted_hits[0]['_source']['details'].keys() == ['information']
        assert sorted_hits[0]['_source']['details']['information'] == 'Example information'

        assert sorted_hits[1].keys() == ['_score', '_type', '_id', '_source', '_index']
        assert type(sorted_hits[1]['_id']) == unicode
        assert sorted_hits[1]['_type'] == 'event'

        assert sorted_hits[1]['_index'] == datetime.now().strftime("events-%Y%m%d")

        assert sorted_hits[1]['_source'].keys() == ['ip', 'details', 'summary']
        assert sorted_hits[1]['_source']['ip'] == '1.2.3.4'
        assert sorted_hits[1]['_source']['summary'] == 'Test Summary'

        assert sorted_hits[1]['_source']['details'].keys() == ['information']
        assert sorted_hits[1]['_source']['details']['information'] == 'Example information'

        assert sorted_hits[2].keys() == ['_score', '_type', '_id', '_source', '_index']
        assert type(sorted_hits[2]['_id']) == unicode
        assert sorted_hits[2]['_type'] == 'event'

        assert sorted_hits[2]['_index'] == datetime.now().strftime("events-%Y%m%d")

        assert sorted_hits[2]['_source'].keys() == ['ip', 'details', 'summary']
        assert sorted_hits[2]['_source']['ip'] == '127.0.0.1'
        assert sorted_hits[2]['_source']['summary'] == 'Test Summary'

        assert sorted_hits[2]['_source']['details'].keys() == ['information']
        assert sorted_hits[2]['_source']['details']['information'] == 'Example information'

        assert results['aggregations'].keys() == ['ip']

        assert results['aggregations']['ip'].keys() == ['terms']

        assert len(results['aggregations']['ip']['terms']) == 2

        results['aggregations']['ip']['terms'].sort()
        assert results['aggregations']['ip']['terms'][0]['count'] == 1
        assert results['aggregations']['ip']['terms'][0]['key'] == '127.0.0.1'

        assert results['aggregations']['ip']['terms'][1]['count'] == 2
        assert results['aggregations']['ip']['terms'][1]['key'] == '1.2.3.4'

    def test_aggregation_without_must_fields(self):
        event = self.generate_default_event()
        event['_source']['utctimestamp'] = event['_source']['utctimestamp']()
        self.populate_test_event(event)
        self.flush(self.event_index_name)

        search_query = SearchQuery(minutes=10)

        search_query.add_aggregation(Aggregation('summary'))
        results = search_query.execute(self.es_client)
        assert results['aggregations']['summary']['terms'][0]['count'] == 1

    def test_aggregation_query_execute(self):
        query = SearchQuery()
        query.add_must(ExistsMatch('note'))
        query.add_aggregation(Aggregation('note'))
        assert query.date_timedelta == {}

        self.populate_example_event()
        self.populate_example_event()
        self.flush(self.event_index_name)

        results = query.execute(self.es_client)
        assert results.keys() == ['hits', 'meta', 'aggregations']
        assert results['meta'].keys() == ['timed_out']
        assert results['meta']['timed_out'] is False

        assert len(results['hits']) == 2

        assert results['hits'][0].keys() == ['_score', '_type', '_id', '_source', '_index']
        assert type(results['hits'][0]['_id']) == unicode
        assert results['hits'][0]['_type'] == 'event'

        assert results['hits'][0]['_index'] == datetime.now().strftime("events-%Y%m%d")

        assert results['hits'][0]['_source'].keys() == ['note', 'details', 'summary']
        assert results['hits'][0]['_source']['note'] == 'Example note'
        assert results['hits'][0]['_source']['summary'] == 'Test Summary'

        assert results['hits'][0]['_source']['details'].keys() == ['information']
        assert results['hits'][0]['_source']['details']['information'] == 'Example information'

        assert results['hits'][1].keys() == ['_score', '_type', '_id', '_source', '_index']
        assert type(results['hits'][1]['_id']) == unicode
        assert results['hits'][1]['_type'] == 'event'

        assert results['hits'][1]['_index'] == datetime.now().strftime("events-%Y%m%d")

        assert results['hits'][1]['_source'].keys() == ['note', 'details', 'summary']
        assert results['hits'][1]['_source']['note'] == 'Example note'
        assert results['hits'][1]['_source']['summary'] == 'Test Summary'

        assert results['hits'][1]['_source']['details'].keys() == ['information']
        assert results['hits'][1]['_source']['details']['information'] == 'Example information'

        assert results['aggregations'].keys() == ['note']

        assert results['aggregations']['note'].keys() == ['terms']

        assert len(results['aggregations']['note']['terms']) == 1

        results['aggregations']['note']['terms'].sort()
        assert results['aggregations']['note']['terms'][0]['count'] == 2
        assert results['aggregations']['note']['terms'][0]['key'] == 'Example note'

    def test_simple_query_execute(self):
        query = SearchQuery()
        query.add_must(ExistsMatch('note'))
        assert query.date_timedelta == {}

        self.populate_example_event()
        self.flush(self.event_index_name)

        results = query.execute(self.es_client)

        assert results.keys() == ['hits', 'meta']
        assert results['meta'].keys() == ['timed_out']
        assert results['meta']['timed_out'] is False
        assert len(results['hits']) == 1

        assert results['hits'][0].keys() == ['_score', '_type', '_id', '_source', '_index']
        assert type(results['hits'][0]['_id']) == unicode
        assert results['hits'][0]['_type'] == 'event'

        assert results['hits'][0]['_index'] == datetime.now().strftime("events-%Y%m%d")

        assert results['hits'][0]['_source'].keys() == ['note', 'details', 'summary']
        assert results['hits'][0]['_source']['note'] == 'Example note'
        assert results['hits'][0]['_source']['summary'] == 'Test Summary'

        assert results['hits'][0]['_source']['details'].keys() == ['information']
        assert results['hits'][0]['_source']['details']['information'] == 'Example information'

        with pytest.raises(KeyError):
            results['abcdefg']

        with pytest.raises(KeyError):
            results['abcdefg']['test']

    def test_beginning_time_seconds(self):
        query = SearchQuery(seconds=10)
        query.add_must(ExistsMatch('summary'))
        assert query.date_timedelta == {'seconds': 10}

        default_event = {
            "utctimestamp": UnitTestSuite.current_timestamp(),
            "summary": "Test summary",
            "details": {
                "note": "Example note",
            }
        }
        self.populate_test_event(default_event)

        too_old_event = default_event
        too_old_event['utctimestamp'] = UnitTestSuite.subtract_from_timestamp({'seconds': 11})
        self.populate_test_event(too_old_event)

        not_old_event = default_event
        not_old_event['utctimestamp'] = UnitTestSuite.subtract_from_timestamp({'seconds': 9})
        self.populate_test_event(not_old_event)

        self.flush(self.event_index_name)

        results = query.execute(self.es_client)
        assert len(results['hits']) == 2

    def test_beginning_time_minutes(self):
        query = SearchQuery(minutes=10)
        query.add_must(ExistsMatch('summary'))
        assert query.date_timedelta == {'minutes': 10}

        default_event = {
            "utctimestamp": UnitTestSuite.current_timestamp(),
            "summary": "Test summary",
            "details": {
                "note": "Example note",
            }
        }

        self.populate_test_event(default_event)
        default_event['utctimestamp'] = UnitTestSuite.subtract_from_timestamp({'minutes': 11})
        self.populate_test_event(default_event)

        not_old_event = default_event
        not_old_event['utctimestamp'] = UnitTestSuite.subtract_from_timestamp({'minutes': 9})
        self.populate_test_event(not_old_event)

        self.flush(self.event_index_name)

        results = query.execute(self.es_client)
        assert len(results['hits']) == 2

    def test_beginning_time_hours(self):
        query = SearchQuery(hours=10)
        query.add_must(ExistsMatch('summary'))
        assert query.date_timedelta == {'hours': 10}

        default_event = {
            "utctimestamp": UnitTestSuite.current_timestamp(),
            "summary": "Test summary",
            "details": {
                "note": "Example note",
            }
        }

        self.populate_test_event(default_event)
        default_event['utctimestamp'] = UnitTestSuite.subtract_from_timestamp({'hours': 11})
        self.populate_test_event(default_event)

        not_old_event = default_event
        not_old_event['utctimestamp'] = UnitTestSuite.subtract_from_timestamp({'hours': 9})
        self.populate_test_event(not_old_event)

        self.flush(self.event_index_name)

        results = query.execute(self.es_client)
        assert len(results['hits']) == 2

    def test_beginning_time_days(self):
        query = SearchQuery(days=10)
        query.add_must(ExistsMatch('summary'))
        assert query.date_timedelta == {'days': 10}

        default_event = {
            "utctimestamp": UnitTestSuite.current_timestamp(),
            "summary": "Test summary",
            "details": {
                "note": "Example note",
            }
        }

        self.populate_test_event(default_event)
        default_event['utctimestamp'] = UnitTestSuite.subtract_from_timestamp({'days': 11})
        self.populate_test_event(default_event)

        not_old_event = default_event
        not_old_event['utctimestamp'] = UnitTestSuite.subtract_from_timestamp({'days': 9})
        self.populate_test_event(not_old_event)

        self.flush(self.event_index_name)

        results = query.execute(self.es_client)
        assert len(results['hits']) == 2

    def test_without_time_defined(self):
        query = SearchQuery()
        query.add_must(ExistsMatch('summary'))
        assert query.date_timedelta == {}

        default_event = {
            "utctimestamp": UnitTestSuite.current_timestamp(),
            "summary": "Test summary",
            "details": {
                "note": "Example note",
            }
        }

        self.populate_test_event(default_event)
        default_event['utctimestamp'] = UnitTestSuite.subtract_from_timestamp({'days': 11})
        self.populate_test_event(default_event)

        not_old_event = default_event
        not_old_event['utctimestamp'] = UnitTestSuite.subtract_from_timestamp({'days': 9})
        self.populate_test_event(not_old_event)

        self.flush(self.event_index_name)

        results = query.execute(self.es_client)
        assert len(results['hits']) == 3

    def test_without_utctimestamp(self):
        query = SearchQuery(days=10)
        query.add_must(ExistsMatch('summary'))
        assert query.date_timedelta == {'days': 10}

        default_event = {
            "timestamp": UnitTestSuite.current_timestamp(),
            "summary": "Test summary",
            "details": {
                "note": "Example note",
            }
        }

        self.populate_test_event(default_event)
        self.flush(self.event_index_name)

        results = query.execute(self.es_client)
        assert len(results['hits']) == 0

    def test_without_queries_and_timestamp(self):
        query = SearchQuery()
        with pytest.raises(AttributeError):
            query.execute(self.es_client)

    def test_without_queries(self):
        query = SearchQuery(minutes=10)
        with pytest.raises(AttributeError):
            query.execute(self.es_client)

    def test_execute_with_size(self):
        for num in range(0, 30):
            self.populate_example_event()
        self.flush(self.event_index_name)
        query = SearchQuery()
        query.add_must(ExistsMatch('summary'))
        results = query.execute(self.es_client, size=12)
        assert len(results['hits']) == 12

    def test_execute_without_size(self):
        for num in range(0, 1200):
            self.populate_example_event()
        self.flush(self.event_index_name)
        query = SearchQuery()
        query.add_must(ExistsMatch('summary'))
        results = query.execute(self.es_client)
        assert len(results['hits']) == 1000

    def test_execute_with_should(self):
        self.populate_example_event()
        self.flush(self.event_index_name)
        self.query.add_should(ExistsMatch('summary'))
        self.query.add_should(ExistsMatch('nonexistentfield'))
        results = self.query.execute(self.es_client)
        assert len(results['hits']) == 1

    def test_beginning_time_seconds_received_timestamp(self):
        query = SearchQuery(seconds=10)
        query.add_must(ExistsMatch('summary'))
        assert query.date_timedelta == {'seconds': 10}

        default_event = {
            "receivedtimestamp": UnitTestSuite.current_timestamp(),
            "summary": "Test summary",
            "details": {
                "note": "Example note",
            }
        }
        self.populate_test_event(default_event)

        too_old_event = default_event
        too_old_event['receivedtimestamp'] = UnitTestSuite.subtract_from_timestamp({'seconds': 11})
        self.populate_test_event(too_old_event)

        not_old_event = default_event
        not_old_event['receivedtimestamp'] = UnitTestSuite.subtract_from_timestamp({'seconds': 9})
        self.populate_test_event(not_old_event)

        self.flush(self.event_index_name)

        results = query.execute(self.es_client)
        assert len(results['hits']) == 2

    def test_time_received_timestamp(self):
        query = SearchQuery(seconds=10)
        query.add_must(ExistsMatch('summary'))
        assert query.date_timedelta == {'seconds': 10}

        received_timestamp_default_event = {
            "receivedtimestamp": UnitTestSuite.current_timestamp(),
            "summary": "Test summary",
            "details": {
                "note": "Example note",
            }
        }
        self.populate_test_event(received_timestamp_default_event)

        utctimestamp_default_event = {
            "utctimestamp": UnitTestSuite.current_timestamp(),
            "summary": "Test summary",
            "details": {
                "note": "Example note",
            }
        }
        self.populate_test_event(utctimestamp_default_event)

        default_event = {
            "utctimestamp": UnitTestSuite.current_timestamp(),
            "receivedtimestamp": UnitTestSuite.current_timestamp(),
            "summary": "Test summary",
            "details": {
                "note": "Example note",
            }
        }
        self.populate_test_event(default_event)

        modified_received_timestamp_event = default_event
        modified_received_timestamp_event['receivedtimestamp'] = UnitTestSuite.subtract_from_timestamp({'seconds': 11})
        self.populate_test_event(modified_received_timestamp_event)

        modified_utc_timestamp_event = default_event
        modified_utc_timestamp_event['utctimestamp'] = UnitTestSuite.subtract_from_timestamp({'seconds': 9})
        self.populate_test_event(modified_utc_timestamp_event)

        self.flush(self.event_index_name)

        results = query.execute(self.es_client)
        assert len(results['hits']) == 5
