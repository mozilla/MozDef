from elasticsearch_dsl import Q, Search, A

import pyes
import pyes_enabled

from utilities.toUTC import toUTC

from datetime import datetime
from datetime import timedelta


def ExistsMatch(field_name):
    if pyes_enabled.pyes_on is True:
        return pyes.ExistsFilter(field_name)
    return Q('exists', field=field_name)


def TermMatch(key, value):
    if pyes_enabled.pyes_on is True:
        return pyes.TermFilter(key, value)
    return Q('match', **{key: value})


def TermsMatch(key, value):
    if pyes_enabled.pyes_on is True:
        return pyes.TermsFilter(key, value)
    return Q('terms', **{key: value})


def WildcardMatch(key, value):
    if pyes_enabled.pyes_on is True:
        return pyes.QueryFilter(pyes.WildcardQuery(key, value))
    return Q('wildcard', **{key: value})


def PhraseMatch(key, value):
    if pyes_enabled.pyes_on is True:
        return pyes.QueryFilter(pyes.MatchQuery(key, value, 'phrase'))
    return Q('match_phrase', **{key: value})


def BooleanMatch(must=[], must_not=[], should=[]):
    if pyes_enabled.pyes_on is True:
        return pyes.BoolFilter(must=must, should=should, must_not=must_not)
    return Q('bool', must=must, must_not=must_not, should=should)


def MissingMatch(field_name):
    if pyes_enabled.pyes_on is True:
        return pyes.filters.MissingFilter(field_name)
    return Q('missing', field=field_name)


def RangeMatch(field_name, from_value, to_value):
    if pyes_enabled.pyes_on is True:
        return pyes.RangeQuery(qrange=pyes.ESRange(field_name, from_value=from_value, to_value=to_value))
    return Q('range', **{field_name: {'gte': from_value, 'lte': to_value}})


def QueryStringMatch(query_str):
    if pyes_enabled.pyes_on is True:
        return pyes.QueryFilter(pyes.QueryStringQuery(query_str))
    return Q('query_string', query=query_str)


def Aggregation(field_name, aggregation_size=20):
    if pyes_enabled.pyes_on is True:
        return field_name, aggregation_size
    return A('terms', field=field_name, size=aggregation_size)


def AggregatedResults(input_results):
    if pyes_enabled.pyes_on is True:
        converted_results = {
            'meta': {
                'timed_out': input_results.timed_out
            },
            'hits': [],
            'aggregations': {}
        }
        for hit in input_results.hits.hits:
            hit_dict = {
                '_id': unicode(hit['_id']),
                '_type': hit['_type'],
                '_index': hit['_index'],
                '_score': hit['_score'],
                '_source': hit['_source'],
            }
            converted_results['hits'].append(hit_dict)

        for facet_name, facet_value in input_results.facets.iteritems():
            aggregation_dict = {
                'terms': []
            }
            for term in facet_value.terms:
                aggregation_dict['terms'].append({'count': term.count, 'key': term.term})
            converted_results['aggregations'][facet_name] = aggregation_dict
    else:
        converted_results = {
            'meta': {
                'timed_out': input_results.timed_out
            },
            'hits': [],
            'aggregations': {}
        }
        for hit in input_results.hits:
            hit_dict = {
                '_id': hit.meta.id,
                '_type': hit.meta.doc_type,
                '_index': hit.meta.index,
                '_score': hit.meta.score,
                '_source': hit.to_dict()
            }
            converted_results['hits'].append(hit_dict)

        for agg_name, aggregation in input_results.aggregations.to_dict().iteritems():
            aggregation_dict = {
                'terms': []
            }
            for bucket in aggregation['buckets']:
                aggregation_dict['terms'].append({'count': bucket['doc_count'], 'key': bucket['key']})

            converted_results['aggregations'][agg_name] = aggregation_dict

    return converted_results


def SimpleResults(input_results):
    if pyes_enabled.pyes_on is True:
        converted_results = {
            'meta': {
                'timed_out': input_results.timed_out
            },
            'hits': []
        }
        for hit in input_results.hits.hits:
            hit_dict = {
                '_id': unicode(hit['_id']),
                '_type': hit['_type'],
                '_index': hit['_index'],
                '_score': hit['_score'],
                '_source': hit['_source'],
            }
            converted_results['hits'].append(hit_dict)
    else:
        converted_results = {
            'meta': {
                'timed_out': input_results.timed_out,
            },
            'hits': []
        }
        for hit in input_results.hits:
            hit_dict = {
                '_id': hit.meta.id,
                '_type': hit.meta.doc_type,
                '_index': hit.meta.index,
                '_score': hit.meta.score,
                '_source': hit.to_dict()
            }

            converted_results['hits'].append(hit_dict)

    return converted_results


class SearchQuery():
    def __init__(self, *args, **kwargs):
        self.date_timedelta = dict(kwargs)
        self.must = []
        self.must_not = []
        self.should = []
        self.aggregation = []

    def append_to_array(self, in_array, in_obj):
        """
        Allow a list or a specific filter/query object to
        get added to build a query
        """
        if isinstance(in_obj, list):
            for key in in_obj:
                in_array.append(key)
        else:
            in_array.append(in_obj)

    def add_must(self, input_obj):
        self.append_to_array(self.must, input_obj)

    def add_must_not(self, input_obj):
        self.append_to_array(self.must_not, input_obj)

    def add_should(self, input_obj):
        self.append_to_array(self.should, input_obj)

    def add_aggregation(self, input_obj):
        self.append_to_array(self.aggregation, input_obj)

    def execute(self, elasticsearch_client, indices=['events', 'events-previous'], size=1000):
        if self.must == [] and self.must_not == [] and self.should == [] and self.aggregation == []:
            raise AttributeError('Must define a must, must_not, should query, or aggregation')

        if self.date_timedelta:
            end_date = toUTC(datetime.now())
            begin_date = toUTC(datetime.now() - timedelta(**self.date_timedelta))
            range_query = RangeMatch('utctimestamp', begin_date, end_date)
            self.add_must(range_query)

        search_query = None
        if pyes_enabled.pyes_on is True:
            search_query = pyes.ConstantScoreQuery(pyes.MatchAllQuery())
            search_query.filters.append(BooleanMatch(must=self.must, should=self.should, must_not=self.must_not))
        else:
            search_query = BooleanMatch(
                must=self.must, must_not=self.must_not, should=self.should)

        results = []
        if len(self.aggregation) == 0:
            results = elasticsearch_client.search(search_query, indices, size)
        else:
            results = elasticsearch_client.aggregated_search(search_query, indices, self.aggregation, size)

        return results
