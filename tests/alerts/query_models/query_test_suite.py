from elasticsearch import Elasticsearch

import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), "../../../alerts/lib"))
from models import SearchQuery
# from query_classes import SearchQuery

from config import ES

# Remove this code when pyes is gone!
import pyes
import pyes_enabled
from config import ESv134
# Remove this code when pyes is gone!


class QueryTestSuite():
    def setup(self):
        self.index_name = "events"

        self.pyes_client = pyes.ES(ESv134['servers'])
        self.es = Elasticsearch(ES['servers'])

        self.reset_elasticsearch()
        self.setup_elasticsearch()

    def populate_test_event(self, event):
        if pyes_enabled.pyes_on is True:
            self.pyes_client.index(index=self.index_name, doc_type='event', doc=event)
            self.pyes_client.indices.flush()

        self.es.index(index=self.index_name, doc_type='event', body=event)
        self.es.indices.flush(index=self.index_name)

    def setup_elasticsearch(self):
        if pyes_enabled.pyes_on is True:
            self.pyes_client.indices.create_index(self.index_name)

        self.es.indices.create(index=self.index_name)

    def reset_elasticsearch(self):
        if pyes_enabled.pyes_on is True:
            self.pyes_client.indices.delete_index_if_exists(self.index_name)
            self.pyes_client.indices.delete_index_if_exists("alerts")

        self.es.indices.delete(index=self.index_name, ignore=[400, 404])
        self.es.indices.delete(index="alerts", ignore=[400, 404])

    def verify_test(self, query_result, positive_test):
        if positive_test:
            if len(query_result) is 1:
                print "\t[SUCCESS]"
            else:
                print "\t[ERROR]"

            assert len(query_result) is 1
        else:
            if len(query_result) is 0:
                print "\t[SUCCESS]"
            else:
                print "\t[ERROR]"

            assert len(query_result) is 0

    def test_query_class(self):
        print ""
        pyes_enabled_values = [True, False]
        for pyes_enable in pyes_enabled_values:
            pyes_enabled.pyes_on = pyes_enable
            if pyes_enable is True:
                self.es_client = self.pyes_client
            else:
                self.es_client = self.es

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
                    print "Testing must test for " + self.__class__.__name__ + " with input: " + str(event) + " " + str(pyes_enabled.pyes_on),
                    self.verify_test(query_result, self.positive_test)

                    # Testing must_not
                    search_query = SearchQuery(minutes=1)
                    search_query.add_must_not(query)
                    query_result = search_query.execute(self.es_client)
                    # replace print statement with a specific py.test unit test, so that it shows up in total tests run
                    print "Testing must_not test for " + self.__class__.__name__ + " with input: " + str(event) + " " + str(pyes_enabled.pyes_on),
                    # print "Testing " +
                    self.verify_test(query_result, self.positive_test is False)

                    # Testing should
                    # todo
                    # Figure out a way to automagically test 'should'

