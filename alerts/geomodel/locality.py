from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, NamedTuple, Optional

from mozdef_util.elasticsearch_client import ElasticsearchClient as ESClient
from mozdef_util.query_models import SearchQuery, TermMatch

import alerts.geomodel.config as config


# Default radius (in Kilometres) that a locality should have.
_DEFAULT_RADIUS_KM = 50.0

# TODO: Switch to dataclasses when we move to Python3.7+

class Locality(NamedTuple):
    '''Represents a specific locality.
    '''

    sourceipaddress: str
    city: str
    country: str
    lastaction: datetime
    latitude: float
    longitude: float
    radius: int

class State(NamedTuple):
    '''Represents the state tracked for each user regarding their localities.
    '''

    type_: str
    username: str
    localities: List[Locality]

class Entry(NamedTuple):
    '''A top-level container for locality state that will be inserted into
    ElasticSearch.
    The `identifier` field here is the `_id` field of the ES document.  When
    this id is `None`, a new document is inserted whereas when the id is known,
    the existing document is updated.
    '''

    identifier: Optional[str]
    state: State

class Update(NamedTuple):
    '''Produced by calls to functions operating on lists of `State`s to
    indicate when an update was applied without having to maintain distinct
    lists.
    '''

    state: State
    did_update: bool

    def flat_map(fn: Callable[[State], 'Update'], u: 'Update') -> 'Update':
        '''Apply a function to a `State` that produces an `Update` against the
        state contained within an established `Update`.  The resulting `Update`
        will have its `did_update` field set to `True` if either the original
        or the new `Update` are `True`.
        '''
        
        new = fn(u.state)

        return Update(new.state, u.did_update or new.did_update)

JournalInterface = Callable[[List[Entry], str], None]
QueryInterface = Callable[[SearchQuery, str], List[Entry]]

def _dict_take(dictionary, keys):
    return {key: dictionary[key] for key in keys}

def _update(state: State, from_evt: State) -> Update:
    did_update = False

    for loc1 in from_evt.localities:
        did_find = False

        for index, loc2 in enumerate(state.localities):
            # If we find that the new state's locality has been recorded
            # for the user in question, we only want to update it if either
            # their IP changed or the new time of activity is more recent.
            if loc1.city == loc2.city and loc1.country == loc2.country:
                did_find = True

                new_more_recent = loc1.lastaction > loc2.lastaction
                new_ip = loc1.sourceipaddress != loc2.sourceipaddress

                if new_more_recent or new_ip:
                    state.localities[index] = loc1
                    did_update = True

                # Stop looking for the locality in the records pulled from ES.
                break
        
        if not did_find:
            state.localities.append(loc1)
            did_update = True

    return Update(state, did_update)

def wrap_journal(client: ESClient) -> JournalInterface:
    '''Wrap an `ElasticsearchClient` in a closure of type `JournalInterface`.
    '''

    def wrapper(entries: List[Entry], esindex: str):
        for entry in entries:
            document = dict(entry.state._asdict())

            client.save_object(
                index=esindex,
                body=document,
                doc_id=entry.identifier)

    return wrapper

def wrap_query(client: ESClient) -> QueryInterface:
    '''Wrap an `ElasticsearchClient` in a closure of type `QueryInterface`.
    '''

    def to_state(result: Dict[str, Any]) -> Optional[State]:
        try:
            result['localities'] = [
                Locality(**_dict_take(loc, Locality._fields))
                for loc in result['localities']
            ]

            return State(**_dict_take(result, State._fields))
        except TypeError:
            return None
        except KeyError:
            return None

    def wrapper(query: SearchQuery, esindex: str) -> List[Entry]:
        results = query.execute(client, indices=[esindex]).get('hits', [])

        entries = []
        for event in results:
            opt_state = to_state(event.get('_source', {}))

            if opt_state is not None:
                entries.append(Entry(event['_id'], opt_state))

        return entries

    return wrapper

def from_event(
        event: Dict[str, Any],
        radius=_DEFAULT_RADIUS_KM
) -> Optional[Locality]:
    '''Extract locality information from an event if it is present in order
    to produce a `Locality` for which an authenticated action was taken.
    '''

    _source = event.get('_source', {})

    source_ip = _source.get('sourceipaddress')
    geo_data = _source.get('sourceipgeolocation')

    if source_ip is None or geo_data is None:
        return None

    # Here we try to extract the time at which the event occurred.
    # Because `%z` only got support for colon-separated UTC offsets
    # (like +00:00) in Python 3.7, we do a little bit of tampering to make the
    # conversion back to a `datetime` as straightforward as possible.
    now = datetime.strftime(datetime.utcnow(), '%Y-%m-%dT%H:%M:%S.%f+00:00')
    active_time_str = _source.get('utctimestamp', now)
    active_time = datetime.strptime(
        ''.join(active_time_str.rsplit(':', 1)),
        '%Y-%m-%dT%H:%M:%S.%f%z')

    return Locality(
        source_ip,
        geo_data.get('city', 'UNKNOWN'),
        geo_data.get('country_code', 'UNKNOWN'),
        active_time,
        geo_data.get('latitude', 0.0),
        geo_data.get('longitude', 0.0),
        radius)

def find_all(
        query_es: QueryInterface,
        username: str,
        locality: config.Localities
) -> List[Entry]:
    '''Retrieve all locality state from ElasticSearch.
    '''

    search = SearchQuery()
    search.add_must([
        TermMatch('type_', 'locality'),
        TermMatch('username', username)
    ])

    return query_es(search, locality.es_index)

def merge(persisted: List[State], event_sourced: List[State]) -> List[Update]:
    '''Merge together a list of states already stored in ElasticSearch
    (obtained via `find_all`) and a list of new states extracted from events.
    This process results in the creation of a new list of states wherein the
    state for each user in either list has had their list of localities updated
    to reflect:

        1. Observations of activity within known localities and
        2. Observations of activity within new localities
    '''

    mapped = {state.username: Update(state, False) for state in persisted}

    for new_state in event_sourced:
        if new_state.username in mapped:
            old_state = mapped[new_state.username].state
            mapped[new_state.username] = _update(old_state, new_state)
        else:
            mapped[new_state.username] = Update(new_state, True)

    return list(mapped.values())

def remove_outdated(state: State, days_valid: int) -> Update:
    '''Update a state by removing localities that are outdated, determined
    by checking if the last activity within a given locality was at least
    some number of days ago.
    '''

    new_localities = [
        loc
        for loc in state.localities
        if loc.lastaction >= datetime.utcnow() - timedelta(days=days_valid)
    ]

    return Update(
        state=State(state.type_, state.username, new_localities),
        did_update=len(new_localities) != len(state.localities))
