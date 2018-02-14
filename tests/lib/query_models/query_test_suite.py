#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
# Copyright (c) 2017 Mozilla Corporation

import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), "../../../lib"))
from query_models import SearchQuery

sys.path.append(os.path.join(os.path.dirname(__file__), "../../"))
from unit_test_suite import UnitTestSuite

import pytest


class QueryTestSuite(UnitTestSuite):

    def verify_test(self, query_result, positive_test):
        assert query_result['meta']['timed_out'] is False
        if positive_test:
            assert len(query_result['hits']) is 1
        else:
            assert len(query_result['hits']) is 0

    def test_query_class(self):
        for query, events in self.query_tests().iteritems():
            for event in events:
                if pytest.config.option.delete_indexes:
                    self.reset_elasticsearch()
                    self.setup_elasticsearch()

                self.populate_test_object(event)
                self.flush(self.event_index_name)

                # Testing must
                search_query = SearchQuery()
                search_query.add_must(query)
                query_result = search_query.execute(self.es_client)
                self.verify_test(query_result, self.positive_test)

                # Testing must_not
                search_query = SearchQuery()
                search_query.add_must_not(query)
                query_result = search_query.execute(self.es_client)
                self.verify_test(query_result, self.positive_test is False)
