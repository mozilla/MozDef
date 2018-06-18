#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
# Copyright (c) 2017 Mozilla Corporation

import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), "../../../lib"))
from query_models import SearchQuery, Aggregation, TermMatch, ExistsMatch

sys.path.append(os.path.join(os.path.dirname(__file__), "../../"))
from unit_test_suite import UnitTestSuite


class TestAggregation(UnitTestSuite):
    def test_simple_aggregation_source_field(self):
        events = [
            {"test": "value", "source": "somesource1"},
            {"test": "value", "source": "anothersource1"},
            {"test": "value", "source": "anothersource1"},
            {"test": "value", "note": "think"},
            {"test": "value", "source": "somesource1 anothersource1"},
        ]
        for event in events:
            self.populate_test_object(event)
        self.flush(self.event_index_name)

        search_query = SearchQuery()
        search_query.add_must(TermMatch('test', 'value'))
        search_query.add_aggregation(Aggregation('source'))
        results = search_query.execute(self.es_client)

        assert results['aggregations'].keys() == ['source']

        assert results['aggregations']['source'].keys() == ['terms']
        assert len(results['aggregations']['source']['terms']) == 3
        assert results['aggregations']['source']['terms'][0].keys() == ['count', 'key']

        assert results['aggregations']['source']['terms'][0]['count'] == 2
        assert results['aggregations']['source']['terms'][0]['key'] == 'anothersource1'

        assert results['aggregations']['source']['terms'][1]['count'] == 1
        assert results['aggregations']['source']['terms'][1]['key'] == 'somesource1'

        assert results['aggregations']['source']['terms'][2]['count'] == 1
        assert results['aggregations']['source']['terms'][2]['key'] == 'somesource1 anothersource1'

    def test_simple_aggregation_note_field(self):
        events = [
            {"test": "value", "note": "abvc"},
            {"test": "value", "note": "abvc"},
            {"test": "value", "note": "think"},
            {"test": "value", "summary": "think"},
            {"test": "value", "note": "abvc space line"},
        ]
        for event in events:
            self.populate_test_object(event)
        self.flush(self.event_index_name)

        search_query = SearchQuery()
        search_query.add_must(TermMatch('test', 'value'))
        search_query.add_aggregation(Aggregation('note'))
        results = search_query.execute(self.es_client)

        assert results['aggregations'].keys() == ['note']

        assert results['aggregations']['note'].keys() == ['terms']
        assert len(results['aggregations']['note']['terms']) == 3
        assert results['aggregations']['note']['terms'][0].keys() == ['count', 'key']

        assert results['aggregations']['note']['terms'][0]['count'] == 2
        assert results['aggregations']['note']['terms'][0]['key'] == 'abvc'

        assert results['aggregations']['note']['terms'][1]['count'] == 1
        assert results['aggregations']['note']['terms'][1]['key'] == 'abvc space line'

        assert results['aggregations']['note']['terms'][2]['count'] == 1
        assert results['aggregations']['note']['terms'][2]['key'] == 'think'

    def test_multiple_aggregations(self):
        events = [
            {"test": "value", "note": "abvc"},
            {"test": "value", "note": "abvc"},
            {"test": "value", "note": "think"},
            {"test": "value", "summary": "think"},
        ]
        for event in events:
            self.populate_test_object(event)
        self.flush(self.event_index_name)

        search_query = SearchQuery()
        search_query.add_must(TermMatch('test', 'value'))
        search_query.add_aggregation(Aggregation('note'))
        search_query.add_aggregation(Aggregation('test'))
        results = search_query.execute(self.es_client)

        aggregation_keys = results['aggregations'].keys()
        aggregation_keys.sort()
        assert aggregation_keys == ['note', 'test']

        assert results['aggregations']['note'].keys() == ['terms']
        assert len(results['aggregations']['note']['terms']) == 2
        assert results['aggregations']['note']['terms'][0].keys() == ['count', 'key']

        assert results['aggregations']['note']['terms'][0]['count'] == 2
        assert results['aggregations']['note']['terms'][0]['key'] == 'abvc'

        assert results['aggregations']['note']['terms'][1]['count'] == 1
        assert results['aggregations']['note']['terms'][1]['key'] == 'think'

        assert results['aggregations']['test'].keys() == ['terms']
        assert len(results['aggregations']['test']['terms']) == 1
        assert results['aggregations']['test']['terms'][0].keys() == ['count', 'key']

        assert results['aggregations']['test']['terms'][0]['count'] == 4
        assert results['aggregations']['test']['terms'][0]['key'] == 'value'

    def test_aggregation_non_existing_term(self):
        events = [
            {"test": "value", "note": "abvc"},
            {"test": "value", "note": "abvc"},
            {"test": "value", "note": "think"},
            {"test": "value", "summary": "think"},
        ]
        for event in events:
            self.populate_test_object(event)
        self.flush(self.event_index_name)

        search_query = SearchQuery()
        search_query.add_must(TermMatch('test', 'value'))
        search_query.add_aggregation(Aggregation('example'))
        results = search_query.execute(self.es_client)

        assert results.keys() == ['hits', 'meta', 'aggregations']
        assert len(results['hits']) == 4
        assert results['aggregations'].keys() == ['example']

        assert results['aggregations']['example'].keys() == ['terms']
        assert results['aggregations']['example']['terms'] == []

    def test_aggregation_multiple_layers(self):
        events = [
            {
                "test": "value",
                "details": {"ip": "127.0.0.1"},
            },
            {
                "test": "value",
                "details": {"ip": "127.0.0.1"},
            },
            {
                "test": "value",
                "details": {"ip": "192.168.1.1"},
            },
        ]

        for event in events:
            self.populate_test_object(event)
        self.flush(self.event_index_name)

        search_query = SearchQuery()
        search_query.add_must(TermMatch('test', 'value'))
        search_query.add_aggregation(Aggregation('details.ip'))
        results = search_query.execute(self.es_client)

        assert results['aggregations'].keys() == ['details.ip']
        assert results['aggregations']['details.ip'].keys() == ['terms']
        assert len(results['aggregations']['details.ip']['terms']) == 2

        assert results['aggregations']['details.ip']['terms'][0]['count'] == 2
        assert results['aggregations']['details.ip']['terms'][0]['key'] == "127.0.0.1"

        assert results['aggregations']['details.ip']['terms'][1]['count'] == 1
        assert results['aggregations']['details.ip']['terms'][1]['key'] == "192.168.1.1"

    def test_aggregation_non_existing_layers_term(self):
        events = [
            {"test": "value", "note": "abvc"},
            {"test": "value", "note": "abvc"},
            {"test": "value", "note": "think"},
            {"test": "value", "summary": "think"},
        ]
        for event in events:
            self.populate_test_object(event)
        self.flush(self.event_index_name)

        search_query = SearchQuery()
        search_query.add_must(TermMatch('test', 'value'))
        search_query.add_aggregation(Aggregation('details.ipinformation'))
        results = search_query.execute(self.es_client)

        assert results['aggregations'].keys() == ['details.ipinformation']
        assert results['aggregations']['details.ipinformation'].keys() == ['terms']
        assert len(results['aggregations']['details.ipinformation']['terms']) == 0

    def test_aggregation_with_default_size(self):
        for num in range(0, 100):
            event = {'keyname': 'value' + str(num)}
            self.populate_test_object(event)
        self.flush(self.event_index_name)

        search_query = SearchQuery()
        search_query.add_must(ExistsMatch('keyname'))
        search_query.add_aggregation(Aggregation('keyname'))
        results = search_query.execute(self.es_client)
        assert len(results['aggregations']['keyname']['terms']) == 20

    def test_aggregation_with_aggregation_size(self):
        for num in range(0, 100):
            event = {'keyname': 'value' + str(num)}
            self.populate_test_object(event)
        self.flush(self.event_index_name)

        search_query = SearchQuery()
        search_query.add_must(ExistsMatch('keyname'))
        search_query.add_aggregation(Aggregation('keyname', 2))
        results = search_query.execute(self.es_client)
        assert len(results['aggregations']['keyname']['terms']) == 2
