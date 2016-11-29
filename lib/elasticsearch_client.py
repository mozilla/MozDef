from query_models import SearchQuery, TermMatch, AggregatedResults, SimpleResults

import json
import logging


# Remove this code when pyes is gone!
import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), "../alerts/lib"))
import pyes_enabled
# Remove this code when pyes is gone!

if pyes_enabled.pyes_on is True:
    import pyes
else:
    from elasticsearch import Elasticsearch
    from elasticsearch_dsl import Search
    from elasticsearch.exceptions import NotFoundError
    from elasticsearch.helpers import bulk, BulkIndexError

from bulk_queue import BulkQueue

logger = logging.getLogger(__name__)
logger.level = logging.DEBUG
formatter = logging.Formatter('%(asctime)s %(name)s %(levelname)s %(message)s')


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
        if pyes_enabled.pyes_on is True:
            # ES v1
            self.es_connection = pyes.ES(servers, bulk_size=bulk_amount)
        else:
            # ES v2 and up
            self.es_connection = Elasticsearch(servers)
            self.es_connection.ping()
        self.bulk_queue = BulkQueue(self, threshold=bulk_amount, flush_time=bulk_refresh_time)

    def delete_index(self, index_name, ignore_fail=False):
        if pyes_enabled.pyes_on is True:
            if ignore_fail is True:
                self.es_connection.indices.delete_index_if_exists(index_name)
            else:
                self.es_connection.indices.delete_index(index_name)
        else:
            ignore_codes = []
            if ignore_fail is True:
                ignore_codes = [400, 404]

            self.es_connection.indices.delete(index=index_name, ignore=ignore_codes)

    def get_indices(self):
        if pyes_enabled.pyes_on is True:
            return self.es_connection.indices.stats()['indices'].keys()
        else:
            return self.es_connection.indices.stats()['indices'].keys()

    def create_index(self, index_name, ignore_fail=False, mapping=None):
        if pyes_enabled.pyes_on is True:
            self.es_connection.indices.create_index(index_name)
        else:
            if not mapping:
                mapping = '''
                {
                  "mappings":{}
                }'''
            self.es_connection.indices.create(index=index_name, update_all_types='true', body=mapping)

    def create_alias(self, alias_name, index_name):
        if pyes_enabled.pyes_on is True:
            self.es_connection.indices.set_alias(alias_name, index_name)
        else:
            if self.es_connection.indices.exists_alias(index='*', name=alias_name):
                self.es_connection.indices.delete_alias(index='*', name=alias_name)

            self.es_connection.indices.put_alias(index=index_name, name=alias_name)

    def get_alias(self, alias_name):
        if pyes_enabled.pyes_on is True:
            return self.es_connection.indices.get_alias(alias_name)
        else:
            return self.es_connection.indices.get_alias(index='*', name=alias_name).keys()

    def flush(self, index_name):
        if pyes_enabled.pyes_on is True:
            self.es_connection.indices.flush()
        else:
            self.es_connection.indices.flush(index=index_name)

    def search(self, search_query, indices, size):
        results = []
        if pyes_enabled.pyes_on is True:
            try:
                esresults = self.es_connection.search(search_query, size=size, indices=','.join(map(str, indices)))
                results = esresults._search_raw()
            except pyes.exceptions.IndexMissingException:
                raise ElasticsearchInvalidIndex(indices)
        else:
            try:
                results = Search(using=self.es_connection, index=indices).params(size=size).filter(search_query).execute()
            except NotFoundError:
                raise ElasticsearchInvalidIndex(indices)

        result_set = SimpleResults(results)
        return result_set

    def aggregated_search(self, search_query, indices, aggregations, size):
        if pyes_enabled.pyes_on is True:
            query = search_query.search()
            for field_name, aggregation_size in aggregations:
                query.facet.add_term_facet(field_name, size=aggregation_size)

            esresults = self.es_connection.search(query, size=size, indices=','.join(map(str, indices)))
            results = esresults._search_raw()
        else:
            search_obj = Search(using=self.es_connection, index=indices).params(size=size)
            query_obj = search_obj.filter(search_query)
            for aggregation in aggregations:
                query_obj.aggs.bucket(name=aggregation.to_dict()['terms']['field'], agg_type=aggregation)
            results = query_obj.execute()

        result_set = AggregatedResults(results)
        return result_set

    def save_documents(self, documents):
        if pyes_enabled.pyes_on is True:
            for document in documents:
                try:
                    self.es_connection.index(index=document['_index'], doc_type=document['_type'], doc=document, id=document['_id'], bulk=True)
                except pyes.exceptions.NoServerAvailable:
                    raise ElasticsearchBadServer()
                except pyes.exceptions.InvalidIndexNameException:
                    raise ElasticsearchInvalidIndex(document['_index'])
                except pyes.exceptions.ElasticSearchException as e:
                    raise ElasticsearchException(e.message)
            self.es_connection.flush_bulk(True)
        else:
            try:
                bulk(self.es_connection, documents)
            except BulkIndexError as e:
                logger.error("Error bulk indexing: " + str(e))

    def start_bulk_timer(self):
        if not self.bulk_queue.started():
            self.bulk_queue.start_timer()

    def bulk_save_object(self, index, doc_type, body, doc_id=None):
        self.start_bulk_timer()

        doc_body = body
        if '_source' in body:
            doc_body = body['_source']
        self.bulk_queue.add(index=index, doc_type=doc_type, body=doc_body, doc_id=doc_id)

    def finish_bulk(self):
        self.bulk_queue.stop_timer()

    def save_object(self, index, doc_type, body, doc_id=None, bulk=False):
        if bulk:
            self.bulk_save_object(index=index, doc_type=doc_type, body=body, doc_id=doc_id)
        else:
            if pyes_enabled.pyes_on is True:
                try:
                    return self.es_connection.index(index=index, doc_type=doc_type, doc=body, id=doc_id)
                except pyes.exceptions.NoServerAvailable:
                    raise ElasticsearchBadServer()
                except pyes.exceptions.InvalidIndexNameException:
                    raise ElasticsearchInvalidIndex(index)
                except pyes.exceptions.ElasticSearchException as e:
                    raise ElasticsearchException(e.message)
            else:
                doc_body = body
                if '_source' in body:
                    doc_body = body['_source']
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

        if pyes_enabled.pyes_on is True:
            return self.es_connection.index(index='kibana-int', doc_type='dashboard', doc=dashboarddata)
        else:
            return self.es_connection.index(index='.kibana', doc_type='dashboard', body=dashboarddata)

    def get_cluster_health(self):
        if pyes_enabled.pyes_on is True:
            escluster = pyes.managers.Cluster(self.es_connection)
            return escluster.health()
        else:
            health_dict = self.es_connection.cluster.health()
            # To line up with the health stats from ES1, we're
            # removing certain keys
            health_dict.pop('active_shards_percent_as_number', None)
            health_dict.pop('delayed_unassigned_shards', None)
            health_dict.pop('number_of_in_flight_fetch', None)
            health_dict.pop('number_of_pending_tasks', None)
            health_dict.pop('task_max_waiting_in_queue_millis', None)

            return health_dict
