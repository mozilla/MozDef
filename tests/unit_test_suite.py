import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), "../alerts/lib"))
from config import ES
sys.path.append(os.path.join(os.path.dirname(__file__), "../lib"))
from elasticsearch_client import ElasticsearchClient

from utilities.toUTC import toUTC

from datetime import datetime
from datetime import timedelta
from dateutil.parser import parse


class UnitTestSuite(object):
    def setup(self):
        print "Setting up unit test suite"
        self.index_name = datetime.now().strftime("events-%Y%m%d")

        # todo: remove once we are able to run unit tests against
        # a live server that won't delete all the data. Depends on when we
        # can use a different index for searching in unit tests.
        for server in ES['servers']:
            if "private.scl3.mozilla.com" in server.lower():
                print "THIS SHOULD NOT BE RUN AGAINST A LIVE TARGET ON MOZILLA NETWORK"
                print '\tThis is because all of the data in ES is reset/deteled'
                print '\twhen unit tests are executed.'
                raise Exception('Using live system in config file for ES servers')

        self.es_client = ElasticsearchClient(ES['servers'])

        self.reset_elasticsearch()
        self.setup_elasticsearch()

    def teardown(self):
        self.reset_elasticsearch()

    def populate_test_event(self, event, event_type='event'):
        self.es_client.save_event(body=event, doc_type=event_type)
        self.es_client.flush(self.index_name)

    def setup_elasticsearch(self):
        self.es_client.create_index(self.index_name)
        self.es_client.create_index('alerts')
        self.es_client.create_alias('events', self.index_name)
        self.es_client.create_alias('events-previous', self.index_name)

    def reset_elasticsearch(self):
        self.es_client.delete_index(self.index_name, True)
        self.es_client.delete_index('alerts', True)
        self.es_client.delete_index('events', True)
        self.es_client.delete_index('events-previous', True)
        # Delete templates
        # self.es_client.delete_template('eventstemplate')
        # self.es_client.delete_template('alertstemplate')

    @staticmethod
    def current_timestamp():
        return toUTC(datetime.now()).isoformat()

    @staticmethod
    def subtract_from_timestamp(date_timedelta, timestamp=None):
        if timestamp is None:
            timestamp = UnitTestSuite.current_timestamp()
        utc_time = parse(timestamp)
        custom_date = utc_time - timedelta(**date_timedelta)
        return custom_date.isoformat()

    @staticmethod
    def current_timestamp_lambda():
        return lambda: UnitTestSuite.current_timestamp()

    @staticmethod
    def subtract_from_timestamp_lambda(date_timedelta, timestamp=None):
        return lambda: UnitTestSuite.subtract_from_timestamp(date_timedelta, timestamp)
