from elasticsearch_dsl import Q, Search


import pyes
import pyes_enabled


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


# Need to fix this
def ExactMatch(key, value):
    if pyes_enabled.pyes_on is True:
        return pyes.QueryFilter(pyes.MatchQuery(key, value, 'boolean'))
    return Q('match', **{key: value})


class SearchQuery():
    def __init__(self, *args, **kwargs):
        self.date_timedelta = dict(kwargs)
        self.must = []
        self.must_not = []
        self.should = []

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

    def execute(self, elasticsearch_client):
        if pyes_enabled.pyes_on is True:
            search_filter = pyes.ConstantScoreQuery(pyes.MatchAllQuery())
            search_filter.filters.append(BooleanMatch(must=self.must, should=self.should, must_not=self.must_not))
            esresults = elasticsearch_client.search(search_filter, size=1000, index='events')
            results = esresults._search_raw()['hits']['hits']
        else:
            main_query = BooleanMatch(must=self.must, must_not=self.must_not, should=self.should)
            ser = Search(using=elasticsearch_client, index="events").query(main_query)
            results = ser.execute().hits.hits
        return results
