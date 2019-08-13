#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# Copyright (c) 2017 Mozilla Corporation


from mozdef_util.utilities.toUTC import toUTC

from datetime import datetime
from datetime import timedelta

from .range_match import RangeMatch
from .boolean_match import BooleanMatch


class SearchQuery(object):
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

    def execute(self, elasticsearch_client, indices=['events', 'events-previous'], size=1000, request_timeout=30):
        if self.must == [] and self.must_not == [] and self.should == [] and self.aggregation == []:
            raise AttributeError('Must define a must, must_not, should query, or aggregation')

        if self.date_timedelta:
            end_date = toUTC(datetime.now())
            begin_date = toUTC(datetime.now() - timedelta(**self.date_timedelta))
            utc_range_query = RangeMatch('utctimestamp', begin_date, end_date)
            received_range_query = RangeMatch('receivedtimestamp', begin_date, end_date)
            range_query = utc_range_query | received_range_query
            self.add_must(range_query)

        search_query = None
        search_query = BooleanMatch(must=self.must, must_not=self.must_not, should=self.should)

        results = []
        if len(self.aggregation) == 0:
            results = elasticsearch_client.search(search_query, indices, size, request_timeout)
        else:
            results = elasticsearch_client.aggregated_search(search_query, indices, self.aggregation, size, request_timeout)

        return results
