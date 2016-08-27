import pytest

from datetime import datetime

import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), "../../lib"))
from query_models import SearchQuery, ExistsMatch, TermMatch, Aggregation
sys.path.append(os.path.join(os.path.dirname(__file__), "../"))
from unit_test_suite import UnitTestSuite


class SearchQueryUnitTest(UnitTestSuite):

    def setup(self):
        super(SearchQueryUnitTest, self).setup()
        self.query = SearchQuery()
        assert self.query.must == []
        assert self.query.must_not == []
        assert self.query.should == []
        assert self.query.aggregation == []


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

    def populate_example_event(self):
        event = {
            'summary': 'Test Summary',
            'note': 'Example note',
            'details': {
                'information': 'Example information'
            }
        }
        self.populate_test_event(event)

    def test_aggregation_query_execute(self):
        self.setup()
        query = SearchQuery()
        assert query.date_timedelta == {}
        query.add_must(ExistsMatch('note'))
        query.add_aggregation(Aggregation('note'))
        self.populate_example_event()
        self.populate_example_event()
        results = query.execute(self.es_client)
        assert results.keys() == ['hits', 'meta', 'aggregations']
        assert results['meta'].keys() == ['timed_out']
        assert results['meta']['timed_out'] is False

        assert len(results['hits']) == 2

        assert results['hits'][0].keys() == ['_score', '_type', '_id', '_source', '_index']
        assert type(results['hits'][0]['_id']) == unicode
        assert results['hits'][0]['_type'] == 'event'

        assert results['hits'][0]['_index'] == datetime.now().strftime("events-%Y%m%d")
        assert results['hits'][0]['_score'] == 1.0

        assert results['hits'][0]['_source'].keys() == ['note', 'details', 'summary']
        assert results['hits'][0]['_source']['note'] == 'Example note'
        assert results['hits'][0]['_source']['summary'] == 'Test Summary'

        assert results['hits'][0]['_source']['details'].keys() == ['information']
        assert results['hits'][0]['_source']['details']['information'] == 'Example information'

        assert results['hits'][1].keys() == ['_score', '_type', '_id', '_source', '_index']
        assert type(results['hits'][1]['_id']) == unicode
        assert results['hits'][1]['_type'] == 'event'

        assert results['hits'][1]['_index'] == datetime.now().strftime("events-%Y%m%d")
        assert results['hits'][1]['_score'] == 1.0

        assert results['hits'][1]['_source'].keys() == ['note', 'details', 'summary']
        assert results['hits'][1]['_source']['note'] == 'Example note'
        assert results['hits'][1]['_source']['summary'] == 'Test Summary'

        assert results['hits'][1]['_source']['details'].keys() == ['information']
        assert results['hits'][1]['_source']['details']['information'] == 'Example information'

        assert results['aggregations'].keys() == ['note']

        assert results['aggregations']['note'].keys() == ['terms']

        assert len(results['aggregations']['note']['terms']) == 2

        results['aggregations']['note']['terms'].sort()
        assert results['aggregations']['note']['terms'][0]['count'] == 2
        assert results['aggregations']['note']['terms'][0]['key'] == 'example'

        assert results['aggregations']['note']['terms'][1]['count'] == 2
        assert results['aggregations']['note']['terms'][1]['key'] == 'note'

    def test_simple_query_execute(self):
        self.setup()
        query = SearchQuery()
        assert query.date_timedelta == {}
        query.add_must(ExistsMatch('note'))
        self.populate_example_event()
        results = query.execute(self.es_client)

        assert results.keys() == ['hits', 'meta']
        assert results['meta'].keys() == ['timed_out']
        assert results['meta']['timed_out'] is False
        assert len(results['hits']) == 1

        assert results['hits'][0].keys() == ['_score', '_type', '_id', '_source', '_index']
        assert type(results['hits'][0]['_id']) == unicode
        assert results['hits'][0]['_type'] == 'event'

        assert results['hits'][0]['_index'] == datetime.now().strftime("events-%Y%m%d")
        assert results['hits'][0]['_score'] == 1.0

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
        assert query.date_timedelta == {'seconds': 10}

        default_event = {
            "utctimestamp": self.current_timestamp(),
            "summary": "Test summary",
            "details": {
                "note": "Example note",
            }
        }
        self.populate_test_event(default_event)

        too_old_event = default_event
        too_old_event['utctimestamp'] = self.subtract_from_timestamp(self.current_timestamp(), {'seconds': 11})
        self.populate_test_event(too_old_event)

        not_old_event = default_event
        not_old_event['utctimestamp'] = self.subtract_from_timestamp(self.current_timestamp(), {'seconds': 9})
        self.populate_test_event(not_old_event)

        query.add_must(ExistsMatch('summary'))

        results = query.execute(self.es_client)
        assert len(results['hits']) == 2

    def test_beginning_time_minutes(self):
        query = SearchQuery(minutes=10)
        assert query.date_timedelta == {'minutes': 10}

        default_event = {
            "utctimestamp": self.current_timestamp(),
            "summary": "Test summary",
            "details": {
                "note": "Example note",
            }
        }

        self.populate_test_event(default_event)
        default_event['utctimestamp'] = self.subtract_from_timestamp(self.current_timestamp(), {'minutes': 11})
        self.populate_test_event(default_event)

        not_old_event = default_event
        not_old_event['utctimestamp'] = self.subtract_from_timestamp(self.current_timestamp(), {'minutes': 9})
        self.populate_test_event(not_old_event)

        query.add_must(ExistsMatch('summary'))

        results = query.execute(self.es_client)
        assert len(results['hits']) == 2

    def test_beginning_time_hours(self):
        query = SearchQuery(hours=10)
        assert query.date_timedelta == {'hours': 10}

        default_event = {
            "utctimestamp": self.current_timestamp(),
            "summary": "Test summary",
            "details": {
                "note": "Example note",
            }
        }

        self.populate_test_event(default_event)
        default_event['utctimestamp'] = self.subtract_from_timestamp(self.current_timestamp(), {'hours': 11})
        self.populate_test_event(default_event)

        not_old_event = default_event
        not_old_event['utctimestamp'] = self.subtract_from_timestamp(self.current_timestamp(), {'hours': 9})
        self.populate_test_event(not_old_event)

        query.add_must(ExistsMatch('summary'))

        results = query.execute(self.es_client)
        assert len(results['hits']) == 2

    def test_beginning_time_days(self):
        query = SearchQuery(days=10)
        assert query.date_timedelta == {'days': 10}

        default_event = {
            "utctimestamp": self.current_timestamp(),
            "summary": "Test summary",
            "details": {
                "note": "Example note",
            }
        }

        self.populate_test_event(default_event)
        default_event['utctimestamp'] = self.subtract_from_timestamp(self.current_timestamp(), {'days': 11})
        self.populate_test_event(default_event)

        not_old_event = default_event
        not_old_event['utctimestamp'] = self.subtract_from_timestamp(self.current_timestamp(), {'days': 9})
        self.populate_test_event(not_old_event)

        query.add_must(ExistsMatch('summary'))

        results = query.execute(self.es_client)
        assert len(results['hits']) == 2

    def test_without_time_defined(self):
        query = SearchQuery()
        assert query.date_timedelta == {}

        default_event = {
            "utctimestamp": self.current_timestamp(),
            "summary": "Test summary",
            "details": {
                "note": "Example note",
            }
        }

        self.populate_test_event(default_event)
        default_event['utctimestamp'] = self.subtract_from_timestamp(self.current_timestamp(), {'days': 11})
        self.populate_test_event(default_event)

        not_old_event = default_event
        not_old_event['utctimestamp'] = self.subtract_from_timestamp(self.current_timestamp(), {'days': 9})
        self.populate_test_event(not_old_event)

        query.add_must(ExistsMatch('summary'))

        results = query.execute(self.es_client)
        assert len(results['hits']) == 3

    def test_without_utctimestamp(self):
        query = SearchQuery(days=10)
        assert query.date_timedelta == {'days': 10}

        default_event = {
            "timestamp": self.current_timestamp(),
            "summary": "Test summary",
            "details": {
                "note": "Example note",
            }
        }

        self.populate_test_event(default_event)

        query.add_must(ExistsMatch('summary'))

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
