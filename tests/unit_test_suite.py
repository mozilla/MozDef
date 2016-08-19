import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), "../alerts/lib"))
from config import ES
sys.path.append(os.path.join(os.path.dirname(__file__), "../lib"))
from elasticsearch_client import ElasticsearchClient

from datetime import datetime


class ElasticsearchException(Exception):
    pass


class UnitTestSuite(object):
    def setup(self):
        self.index_name = datetime.now().strftime("events-%Y%m%d")

        self.es_client = ElasticsearchClient(ES['servers'])

        self.reset_elasticsearch()
        self.setup_elasticsearch()

    def teardown(self):
        self.reset_elasticsearch()

    def populate_test_event(self, event, event_type='event'):
        self.es_client.save_event(event, event_type)
        self.es_client.flush(self.index_name)

    def setup_elasticsearch(self):
        self.es_client.create_index(self.index_name)
        self.es_client.create_alias('events', self.index_name)
        self.es_client.create_alias('events-previous', self.index_name)

    def reset_elasticsearch(self):
        self.es_client.delete_index(self.index_name, True)
        self.es_client.delete_index('events', True)
        self.es_client.delete_index('events-previous', True)
        self.es_client.delete_index('alerts', True)

