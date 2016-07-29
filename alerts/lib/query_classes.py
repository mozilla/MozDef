import pyes


class TermFilter(pyes.TermFilter):
    pass


class QueryFilter(pyes.QueryFilter):
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


class SearchQuery():
    def __init__(self, *args, **kwargs):
        self.date_timedelta = dict(kwargs)
        self.must = []
        self.must_not = []
        self.should = []

    def add_must(self, input_obj):
        self.must.append(input_obj)

    def add_musts(self, input_obj):
        for key in input_obj:
            self.add_must(key)

    def add_must_not(self, input_obj):
        self.must_not.append(input_obj)

    def add_must_nots(self, input_obj):
        for key in input_obj:
            self.add_must_not(key)

    def add_should(self, input_obj):
        self.should.append(input_obj)

    def add_shoulds(self, input_obj):
        for key in input_obj:
            self.add_should(key)

