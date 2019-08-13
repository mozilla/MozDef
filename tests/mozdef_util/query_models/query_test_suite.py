#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# Copyright (c) 2017 Mozilla Corporation

from mozdef_util.query_models import SearchQuery

from tests.unit_test_suite import UnitTestSuite


class QueryTestSuite(UnitTestSuite):

    def verify_test(self, query_result, positive_test):
        assert query_result['meta']['timed_out'] is False
        if positive_test:
            assert len(query_result['hits']) is 1
        else:
            assert len(query_result['hits']) is 0

    def test_query_class(self):
        for testcase in self.query_tests():
            query = testcase[0]
            events = testcase[1]
            for event in events:
                if self.config_delete_indexes:
                    self.reset_elasticsearch()
                    self.setup_elasticsearch()

                self.populate_test_object(event)
                self.refresh(self.event_index_name)

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
