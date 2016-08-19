import os
import sys
# sys.path.append(os.path.join(os.path.dirname(__file__), "../../alerts/lib"))
sys.path.append(os.path.join(os.path.dirname(__file__), "../../lib"))
from query_models import SearchQuery

sys.path.append(os.path.join(os.path.dirname(__file__), "../"))
from unit_test_suite import UnitTestSuite


class QueryTestSuite(UnitTestSuite):

    def verify_test(self, query_result, positive_test):
        if positive_test:
            # if len(query_result) is 1:
            #     print "\t[SUCCESS]"
            # else:
            #     print "\t[ERROR]"

            assert len(query_result) is 1
        else:
            # if len(query_result) is 0:
            #     print "\t[SUCCESS]"
            # else:
            #     print "\t[ERROR]"

            assert len(query_result) is 0

    def test_query_class(self):
        # print ""
        for query, events in self.query_tests().iteritems():
            for event in events:
                self.reset_elasticsearch()
                self.setup_elasticsearch()

                self.populate_test_event(event)

                # Testing must
                search_query = SearchQuery(minutes=1)
                search_query.add_must(query)
                query_result = search_query.execute(self.es_client)
                # replace print statement with a specific py.test unit test, so that it shows up in total tests run
                # print "Testing must test for " + self.__class__.__name__ + " with input: " + str(event),
                self.verify_test(query_result, self.positive_test)

                # Testing must_not
                search_query = SearchQuery(minutes=1)
                search_query.add_must_not(query)
                query_result = search_query.execute(self.es_client)
                # replace print statement with a specific py.test unit test, so that it shows up in total tests run
                # print "Testing must_not test for " + self.__class__.__name__ + " with input: " + str(event),
                self.verify_test(query_result, self.positive_test is False)

                # Testing should
                # todo
                # Figure out a way to automagically test 'should'



