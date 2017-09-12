import json

from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search
from elasticsearch.exceptions import NotFoundError
from elasticsearch.helpers import bulk, BulkIndexError

from query_models import SearchQuery, TermMatch, AggregatedResults, SimpleResults
from bulk_queue import BulkQueue

from utilities.logger import logger, initLogger


class ElasticsearchBadServer(Exception):
    def __str__(self):
        return "Bad ES Server defined"


class ElasticsearchException(Exception):
    def __str__(self):
        return "Exception in ES encountered"


class ElasticsearchInvalidIndex(Exception):
    def __init__(self, index_name):
        self.index_name = index_name

    def __str__(self):
        return "Invalid index: " + str(self.index_name)


class ElasticsearchClient():

    def __init__(self, servers, bulk_amount=100, bulk_refresh_time=30):
        self.es_connection = Elasticsearch(servers)
        self.es_connection.ping()
        self.bulk_queue = BulkQueue(self, threshold=bulk_amount, flush_time=bulk_refresh_time)
        initLogger()

    def delete_index(self, index_name, ignore_fail=False):
        ignore_codes = []
        if ignore_fail is True:
            ignore_codes = [400, 404]

        self.es_connection.indices.delete(index=index_name, ignore=ignore_codes)

    def get_indices(self):
        return self.es_connection.indices.stats()['indices'].keys()

    def create_index(self, index_name, ignore_fail=False, mapping=None):
        if not mapping:
            mapping = '''
            {
              "mappings":{}
            }'''
        self.es_connection.indices.create(index=index_name, update_all_types='true', body=mapping)

    def create_alias(self, alias_name, index_name):
        if self.es_connection.indices.exists_alias(index='*', name=alias_name):
            self.es_connection.indices.delete_alias(index='*', name=alias_name)

        self.es_connection.indices.put_alias(index=index_name, name=alias_name)

    def create_alias_multiple_indices(self, alias_name, indices):
        if self.es_connection.indices.exists_alias(index='*', name=alias_name):
            self.es_connection.indices.delete_alias(index='*', name=alias_name)
        for index in indices:
            self.es_connection.indices.put_alias(index=index, name=alias_name)

    def get_alias(self, alias_name):
        return self.es_connection.indices.get_alias(index='*', name=alias_name).keys()

    def flush(self, index_name):
        self.es_connection.indices.flush(index=index_name)

    def search(self, search_query, indices, size):
        results = []
        try:
            results = Search(using=self.es_connection, index=indices).params(size=size).filter(search_query).execute()
        except NotFoundError:
            raise ElasticsearchInvalidIndex(indices)

        result_set = SimpleResults(results)
        return result_set

    def aggregated_search(self, search_query, indices, aggregations, size):
        search_obj = Search(using=self.es_connection, index=indices).params(size=size)
        query_obj = search_obj.filter(search_query)
        for aggregation in aggregations:
            query_obj.aggs.bucket(name=aggregation.to_dict()['terms']['field'], agg_type=aggregation)
        results = query_obj.execute()

        result_set = AggregatedResults(results)
        return result_set

    def save_documents(self, documents):
        try:
            bulk(self.es_connection, documents)
        except BulkIndexError as e:
            logger.error("Error bulk indexing: " + str(e))

    def start_bulk_timer(self):
        if not self.bulk_queue.started():
            self.bulk_queue.start_timer()

    def bulk_save_object(self, index, doc_type, body, doc_id=None):
        self.start_bulk_timer()
        self.bulk_queue.add(index=index, doc_type=doc_type, body=body, doc_id=doc_id)

    def finish_bulk(self):
        self.bulk_queue.stop_timer()

    def save_object(self, index, doc_type, body, doc_id=None, bulk=False):
        # Try and parse it as json if it's a string
        if type(body) is str:
            body = json.loads(body)

        if '_type' in body:
            doc_type = body['_type']

        doc_body = body
        if '_source' in body:
            doc_body = body['_source']

        if bulk:
            self.bulk_save_object(index=index, doc_type=doc_type, body=doc_body, doc_id=doc_id)
        else:
            return self.es_connection.index(index=index, doc_type=doc_type, id=doc_id, body=doc_body)

    def save_alert(self, body, index='alerts', doc_type='alert', doc_id=None, bulk=False):
        return self.save_object(index=index, doc_type=doc_type, body=body, doc_id=doc_id, bulk=bulk)

    def save_event(self, body, index='events', doc_type='event', doc_id=None, bulk=False):
        return self.save_object(index=index, doc_type=doc_type, body=body, doc_id=doc_id, bulk=bulk)

    def get_object_by_id(self, object_id, indices):
        id_match = TermMatch('_id', object_id)
        search_query = SearchQuery()
        search_query.add_must(id_match)
        results = search_query.execute(self, indices=indices)
        if len(results['hits']) == 0:
            return None
        else:
            return results['hits'][0]

    def get_alert_by_id(self, alert_id):
        return self.get_object_by_id(alert_id, ['alerts'])

    def get_event_by_id(self, event_id):
        return self.get_object_by_id(event_id, ['events'])

    def save_dashboard(self, dash_file, dash_name=None):
        f = open(dash_file)
        dashboardjson = json.load(f)
        f.close()
        title = dashboardjson['title']
        if dash_name:
            title = dash_name
        dashboarddata = {
            "user": "guest",
            "group": "guest",
            "title": title,
            "dashboard": json.dumps(dashboardjson)
        }

        return self.es_connection.index(index='.kibana', doc_type='dashboard', body=dashboarddata)

    def get_cluster_health(self):
        health_dict = self.es_connection.cluster.health()
        # To line up with the health stats from ES1, we're
        # removing certain keys
        health_dict.pop('active_shards_percent_as_number', None)
        health_dict.pop('delayed_unassigned_shards', None)
        health_dict.pop('number_of_in_flight_fetch', None)
        health_dict.pop('number_of_pending_tasks', None)
        health_dict.pop('task_max_waiting_in_queue_millis', None)

        return health_dict
