from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search

# Remove this code when pyes is gone!
import pyes
import pyes_enabled
from config import ESv134
import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), "../alerts/lib"))
# Remove this code when pyes is gone!

from query_models import TermMatch, SearchQuery, BooleanMatch


class ElasticsearchClient():

    def __init__(self, servers):
        if pyes_enabled.pyes_on is True:
            # ES v1
            self.pyes_client = pyes.ES(ESv134['servers'])
        else:
            # ES v2 and up
            self.es = Elasticsearch(servers)
            self.es.ping()

    def delete_index(self, index_name, ignore_fail=False):
        if pyes_enabled.pyes_on is True:
            if ignore_fail is True:
                self.pyes_client.indices.delete_index_if_exists(index_name)
            else:
                self.pyes_client.indices.delete_index(index_name)
        else:
            ignore_codes = []
            if ignore_fail is True:
                ignore_codes = [400, 404]

            self.es.indices.delete(index=index_name, ignore=ignore_codes)

    def create_index(self, index_name, ignore_fail=False):
        if pyes_enabled.pyes_on is True:
            self.pyes_client.indices.create_index(index_name)
        else:
            mapping = '''
            {
              "mappings":{}
            }'''
            self.es.indices.create(index=index_name, update_all_types='true', body=mapping)

    def create_alias(self, alias_name, index_name):
        if pyes_enabled.pyes_on is True:
            self.pyes_client.indices.add_alias(alias_name, index_name)
        else:
            self.es.indices.put_alias(index=index_name, name=alias_name)

    def flush(self, index_name):
        if pyes_enabled.pyes_on is True:
            self.pyes_client.indices.flush()
        else:
            self.es.indices.flush(index=index_name)

    def save_event(self, event, event_type='event'):
        if pyes_enabled.pyes_on is True:
            return self.pyes_client.index(index='events', doc_type=event_type, doc=event)
        else:
            return self.es.index(index='events', doc_type=event_type, body=event)

    def update_event(self, index, doc_type, event_id, event):
        if pyes_enabled.pyes_on is True:
            self.pyes_client.update(index, doc_type,event_id, document=event)
        else:
            self.es.index(index=index, doc_type=doc_type, id=event_id, body=event)

    def search(self, search_query, indices=['events']):
        results = []
        if pyes_enabled.pyes_on is True:
            esresults = self.pyes_client.search(search_query, size=1000, indices=','.join(map(str, indices)))
            results = esresults._search_raw()['hits']['hits']
        else:
            esresults = Search(using=self.es, index=indices).query(search_query).execute()
            results = esresults.hits.hits

        return results

    def save_alert(self, alert):
        if pyes_enabled.pyes_on is True:
            return self.pyes_client.index(index='alerts', doc_type='alert', doc=alert)
        else:
            return self.es.index(index='alerts', doc_type='alert', body=alert)

    def get_alert(self, alert_id):
        # todo Improve this
        if pyes_enabled.pyes_on is True:
            tmatch = TermMatch('_id', alert_id)
            search_query = pyes.ConstantScoreQuery(pyes.MatchAllQuery())
            search_query.filters.append(BooleanMatch(must=[tmatch], should=[], must_not=[]))
            import time
            time.sleep(1)
            return self.search(search_query, ['alerts'])[0]
        else:
            tmatch = BooleanMatch(must=[TermMatch('_id', alert_id)])
            import time
            time.sleep(1)
            return self.search(tmatch, ['alerts'])[0]

