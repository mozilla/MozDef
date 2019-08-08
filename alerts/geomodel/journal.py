'''To make GeoModel code more testable, we abstract interaction with
ElasticSearch away via a "journal interface".  This is just a function that,
called with an ES index and a list of `Entry`, stores the contained locality
state data in ElasticSearch.
'''

from typing import Callable, List, NamedTuple, Optional

from mozdef_util.elasticsearch_client import ElasticsearchClient as ESClient

from alerts.geomodel.locality import State


# TODO: Switch to dataclasses when we upgrade to Python 3.7+

class Entry(NamedTuple):
    '''A top-level container for locality state that will be inserted into
    ElasticSearch.
    The `identifier` field here is the `_id` field of the ES document.  When
    this id is `None`, a new document is inserted whereas when the id is known,
    the existing document is updated.
    '''

    identifier: Optional[str]
    state: State

JournalInterface = Callable[[List[Entry], str]]

def wrap(client: ESClient) -> JournalInterface:
    '''Wrap an `ElasticsearchClient` in a closure of type `JournalInterface`.
    '''

    def wrapper(entries: List[Entry], esindex: str):
        for entry in entries:
            document = dict(entry.state._asdict())

            client.save_object(
                index=esindex,
                body=document,
                doc_id=entry.identifer)

    return wrapper
