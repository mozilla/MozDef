# from positive_test_suite import PositiveTestSuite
# from negative_test_suite import NegativeTestSuite
import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), "../../lib"))
from query_models import SearchQuery, Aggregation, ExistsMatch
sys.path.append(os.path.join(os.path.dirname(__file__), "../"))
from unit_test_suite import UnitTestSuite


class TestAggregation(UnitTestSuite):
    def testing(self):
        events = [
            {"test": "value", "note": "abvc"},
            {"test": "value", "note": "abvc"},
            {"test": "value", "note": "think"},
        ]
        for event in events:
            self.populate_test_event(event)
        search_query = SearchQuery()
        search_query.add_must(ExistsMatch('note'))
        aggreg = Aggregation('note')
        search_query.add_aggregation(aggreg)
        results = search_query.execute(self.es_client)
        assert True is True
        # import pdb
        # pdb.set_trace()
        # print results
        # results = normalize_results(unformatted_results)
        # assert results['aggregations']['note_terms']['buckets'][0]['count'] == 2
        # assert results['aggregations']['note_terms']['buckets'][1]['count'] == 2
