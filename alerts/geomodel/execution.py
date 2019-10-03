from datetime import datetime
from typing import Callable, NamedTuple, Optional

from mozdef_util.elasticsearch_client import ElasticsearchClient as ESClient
from mozdef_util.query_models import SearchQuery, TermMatch
from mozdef_util.utilities.toUTC import toUTC


_TYPE_NAME = 'execution_state'


class ExecutionState(NamedTuple):
    '''A record of an alert's execution at a particular time, used to create a
    sliding window through which an alert can query for relevant events and
    not run the risk of missing any due to relying only on searching some
    configured amount of time in the past.
    '''

    type_: str
    #  alert_name: str
    execution_time: datetime

    def new(executed_at: Optional[datetime]=None) -> 'ExecutionState':
        '''Construct a new `ExecutionState` representing the execution of an
        alert at a specific time.
        By default, the execution time will be set to when this function is
        called if not explicitly provided.
        '''

        if executed_at is None:
            executed_at = toUTC(datetime.now())

        return ExecutionState(_TYPE_NAME, executed_at)


class Record(NamedTuple):
    '''A container for data identifying an `ExecutionState` in ElasticSearch.
    '''

    identifier: Optional[str]
    state: ExecutionState

    def new(state: ExecutionState) -> 'Record':
        '''Construct a new `Record` that, when stored, will result in a new
        document being inserted into ElasticSearch.
        '''

        return Record('', state)


Index = str
StoreInterface = Callable[[Record, Index], None]
LoadInterface = Callable[[Index], Optional[Record]]


def _dict_take(dictionary, keys):
    return {key: dictionary[key] for key in keys}


def store(client: ESClient) -> StoreInterface:
    '''Wrap an `ElasticsearchClient` in a `StoreInterface` closure to be
    invoked without requiring direct access to the client in order to
    persist an `ExecutionState`.
    '''

    def wrapper(record: Record, esindex: Index):
        doc = dict(record.state._asdict())

        client.save_object(index=esindex, body=doc, doc_id=record.identifier)

    return wrapper


def load(client: ESClient) -> LoadInterface:
    '''Wrap an `ElasticsearchClient` in a `LoadInterface` closure to be
    invoed without requiring direct access to the client in order to retrieve
    an `ExecutionState`.
    '''

    def wrapper(esindex: Index=None) -> Optional[Record]:
        query = SearchQuery()
        query.add_must(TermMatch('type_', _TYPE_NAME))

        results = query.execute(client, indices=[esindex])

        if len(results['hits']) == 0:
            return None

        eid = results['hits'][0]['_id']

        state = ExecutionState(**_dict_take(
            results['hits'][0].get('_source', {}),
            ExecutionState._fields))

        return Record(eid, state)

    return wrapper
