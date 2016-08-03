import pyes

# This file is to ease the transition from pyes to elasticsearch_dsl
# eventually, this file should go away and move into a folder
class TermFilter(pyes.TermFilter):
    pass


class TermsFilter(pyes.TermsFilter):
    pass


class QueryFilter(pyes.QueryFilter):
    pass


class QueryStringQuery(pyes.QueryStringQuery):
    pass


class MatchQuery(pyes.MatchQuery):
    pass


class ExistsFilter(pyes.ExistsFilter):
    pass


class ESRange(pyes.ESRange):
    pass


class ConstantScoreQuery(pyes.ConstantScoreQuery):
    pass


class RangeQuery(pyes.RangeQuery):
    pass


class MatchAllQuery(pyes.MatchAllQuery):
    pass


class BoolFilter(pyes.BoolFilter):
    pass


class MissingFilter(pyes.filters.MissingFilter):
    pass


class ESClient(pyes.ES):
    pass


class WildcardQuery(pyes.WildcardQuery):
    pass


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

