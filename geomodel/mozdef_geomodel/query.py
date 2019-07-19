'''To make GeoModel code more testable, we abstract interaction with
ElasticSearch away via a "query interface".  This is just a function that,
called with a list of ES indices and a `SearchQuery`, produces a list of
dictionaries as output.
'''

from typing import Any, Callable, List

from mozdef_util.elasticsearch_client import ElasticsearchClient as ESClient
from mozdef_util.query_models import SearchQuery


QueryInterface = Callable[[SearchQuery, List[str]], List[Dict[str, Any]]]


def wrap(client: ESClient) -> QueryInterface:
    '''Wrap an `ElasticsearchClient` in a closure of type `QueryInterface`.
    '''
    
    def wrapper(query: SearchQuery, esindex: str) -> List[Event]:
        return query.execute(client, indices=[esindex])

    return wrapper
