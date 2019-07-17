import json

from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search
from elasticsearch.exceptions import NotFoundError
from elasticsearch.helpers import bulk, BulkIndexError

from .query_models import SearchQuery, TermMatch, AggregatedResults, SimpleResults
from .bulk_queue import BulkQueue

from .utilities.logger import logger

from .event import Event

DOCUMENT_TYPE = '_doc'


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

    def close_index(self, index_name):
        return self.es_connection.indices.close(index=index_name)

    def open_index(self, index_name):
        return self.es_connection.indices.open(index=index_name)

    def delete_index(self, index_name, ignore_fail=False):
        ignore_codes = []
        if ignore_fail is True:
            ignore_codes = [400, 404]
        self.es_connection.indices.delete(index=index_name, ignore=ignore_codes)

    def get_indices(self):
        # Includes open and closed indices
        return list(self.es_connection.indices.get_alias('*', params=dict(expand_wildcards='all')).keys())

    def index_exists(self, index_name):
        return self.es_connection.indices.exists(index_name)

    def create_index(self, index_name, index_config=None):
        if not index_config:
            index_config = '''
            {
              "mappings":{}
            }'''
        self.es_connection.indices.create(index=index_name, body=index_config)

    def create_alias(self, alias, index):
        actions = []
        if self.es_connection.indices.exists_alias('*', alias):
            actions.append({
                'remove': {'index': '*', 'alias': alias}
            })

        actions.append({
            'add': {'index': index, 'alias': alias}
        })
        self.es_connection.indices.update_aliases(dict(actions=actions))

    def create_alias_multiple_indices(self, alias_name, indices):
        actions = []
        if self.es_connection.indices.exists_alias('*', alias_name):
            actions.append({
                'remove': {'index': '*', 'alias': alias_name}
            })

        for index in indices:
            actions.append({'add': {'index': index, 'alias': alias_name}})
        self.es_connection.indices.update_aliases(dict(actions=actions))

    def get_alias(self, alias_name):
        return list(self.es_connection.indices.get_alias(index='*', name=alias_name).keys())

    def get_aliases(self):
        return list(self.es_connection.cat.stats()['indices'].keys())

    def refresh(self, index_name):
        self.es_connection.indices.refresh(index=index_name)

    def search(self, search_query, indices, size, request_timeout):
        results = []
        try:
            results = Search(using=self.es_connection, index=indices).params(size=size, request_timeout=request_timeout).filter(search_query).execute()
        except NotFoundError:
            raise ElasticsearchInvalidIndex(indices)

        result_set = SimpleResults(results)
        return result_set

    def aggregated_search(self, search_query, indices, aggregations, size, request_timeout):
        search_obj = Search(using=self.es_connection, index=indices).params(size=size, request_timeout=request_timeout)
        query_obj = search_obj.filter(search_query)
        for aggregation in aggregations:
            query_obj.aggs.bucket(name=aggregation.to_dict()['terms']['field'], agg_type=aggregation)
        results = query_obj.execute()

        result_set = AggregatedResults(results)
        return result_set

    def save_documents(self, documents):
        # ES library still requires _type to be set
        for document in documents:
            document['_type'] = DOCUMENT_TYPE
        try:
            bulk(self.es_connection, documents)
        except BulkIndexError as e:
            logger.error("Error bulk indexing: " + str(e))

    def finish_bulk(self):
        self.bulk_queue.flush()
        self.bulk_queue.stop_thread()

    def __bulk_save_document(self, index, body, doc_id=None):
        if not self.bulk_queue.started():
            self.bulk_queue.start_thread()
        self.bulk_queue.add(index=index, body=body, doc_id=doc_id)

    def __save_document(self, index, body, doc_id=None, bulk=False):
        if bulk:
            self.__bulk_save_document(index=index, body=body, doc_id=doc_id)
        else:
            # ES library still requires _type to be set
            return self.es_connection.index(index=index, doc_type=DOCUMENT_TYPE, id=doc_id, body=body)

    def __parse_document(self, body):
        if type(body) is str:
            body = json.loads(body)

        doc_body = body
        if '_source' in body:
            doc_body = body['_source']
        return doc_body

    def save_object(self, body, index, doc_id=None, bulk=False):
        doc_body = self.__parse_document(body)
        return self.__save_document(index=index, body=doc_body, doc_id=doc_id, bulk=bulk)

    def save_alert(self, body, index='alerts', doc_id=None, bulk=False):
        doc_body = self.__parse_document(body)
        return self.__save_document(index=index, body=doc_body, doc_id=doc_id, bulk=bulk)

    def save_event(self, body, index='events', doc_id=None, bulk=False):
        doc_body = self.__parse_document(body)
        event = Event(doc_body)
        event.add_required_fields()
        return self.__save_document(index=index, body=event, doc_id=doc_id, bulk=bulk)

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
