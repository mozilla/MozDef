import math
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, NamedTuple, Optional

from mozdef_util.elasticsearch_client import ElasticsearchClient as ESClient
from mozdef_util.utilities.toUTC import toUTC
from mozdef_util.query_models import SearchQuery, TermMatch


# Default radius (in Kilometres) that a locality should have.
_DEFAULT_RADIUS_KM = 50.0

_EARTH_RADIUS = 6373.0  # km # approximate

# TODO: Switch to dataclasses when we move to Python3.7+


class Coordinates(NamedTuple):
    '''Represents geographical coordinates used for distance calculations.
    '''

    latitude: float
    longitude: float


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

    def index_name():
        '''Locality state is stored in an index called "locality" that used to
        be stored in a magic string.
        '''

        return 'locality'


class State(NamedTuple):
    '''Represents the state tracked for each user regarding their localities.
    '''

    type_: str  # Not used here, but we want it in ES.
    username: str
    localities: List[Locality]

    def new(username: str, localities: List[Locality]) -> 'State':
        '''Construct a new State with all fields populated.
        '''

        return State(Locality.index_name(), username, localities)


class Entry(NamedTuple):
    '''A top-level container for locality state that will be inserted into
    ElasticSearch.
    The `identifier` field here is the `_id` field of the ES document.  When
    this id is `None`, a new document is inserted whereas when the id is known,
    the existing document is updated.
    '''

    identifier: Optional[str]
    state: State

    def new(state: State) -> 'Entry':
        '''Construct a new `Entry` that, when journaled, will result in a new
        state entry being recorded rather than replacing an existing one.
        '''

        return Entry('', state)


class Update(NamedTuple):
    '''Produced by calls to functions operating on lists of `State`s to
    indicate when an update was applied without having to maintain distinct
    lists.
    '''

    state: State
    did_update: bool


JournalInterface = Callable[[Entry, str], None]
QueryInterface = Callable[[SearchQuery, str], Optional[Entry]]


def _dict_take(dictionary, keys):
    return {key: dictionary[key] for key in keys}


def wrap_journal(client: ESClient) -> JournalInterface:
    '''Wrap an `ElasticsearchClient` in a closure of type `JournalInterface`.
    '''

    def wrapper(entry: Entry, esindex: str):
        document = dict(entry.state._asdict())

        _id = '' if entry.identifier is None else entry.identifier

        client.save_object(
            index=esindex,
            body=document,
            doc_id=_id)

    return wrapper


def wrap_query(client: ESClient) -> QueryInterface:
    '''Wrap an `ElasticsearchClient` in a closure of type `QueryInterface`.
    '''

    def wrapper(query: SearchQuery, esindex: str) -> Optional[Entry]:
        results = query.execute(client, indices=[esindex]).get('hits', [])

        if len(results) == 0:
            return None

        state_dict = results[0].get('_source', {})
        try:
            state_dict['localities'] = [
                # Convert dictionary localities into `Locality`s after
                # parsing the `datetime` from `lastaction`.
                Locality(**_dict_take({
                    k: v if k != 'lastaction' else toUTC(v)
                    for k, v in loc.items()
                }, Locality._fields))
                for loc in state_dict['localities']
            ]

            eid = results[0]['_id']
            state = State.new(state_dict['username'], state_dict['localities'])

            return Entry(eid, state)
        except TypeError:
            return None
        except KeyError:
            return None

    return wrapper


def from_event(
        event: Dict[str, Any],
        radius=_DEFAULT_RADIUS_KM
) -> Optional[Locality]:
    '''Extract locality information from an event if it is present in order
    to produce a `Locality` for which an authenticated action was taken.
    '''

    _source = event.get('_source', {})
    details = _source.get('details', {})
    source_ip = details.get('sourceipaddress')
    geo_data = details.get('sourceipgeolocation')

    if source_ip is None or geo_data is None:
        return None

    now = toUTC(datetime.now()).isoformat()
    active_time_str = _source.get('utctimestamp', now)
    active_time = toUTC(active_time_str)

    (city, country, lat, lon) = (
        geo_data.get('city'),
        geo_data.get('country_code'),
        geo_data.get('latitude'),
        geo_data.get('longitude')
    )

    if any([v is None for v in [city, country, lat, lon]]):
        return None

    return Locality(source_ip, city, country, active_time, lat, lon, radius)


def find(qes: QueryInterface, username: str, index: str) -> Optional[Entry]:
    '''Retrieve the locality state for one user from ElasticSearch.
    '''

    search = SearchQuery()
    search.add_must([
        TermMatch('type_', Locality.index_name()),
        TermMatch('username', username)
    ])

    return qes(search, index)


def update(state: State, from_evt: State) -> Update:
    '''Update the localities stored under an existing `State` against those
    contained in a new `State` constructed from events.
    '''

    did_update = False

    for loc1 in from_evt.localities:
        did_find = False

        for index, loc2 in enumerate(state.localities):
            # If we find that the new state's locality has been recorded
            # for the user in question, we only want to update it if either
            # their IP changed or the new time of activity is more recent.
            coord1 = _coordinates(loc1)
            coord2 = _coordinates(loc2)

            if distance(coord1, coord2) <= min(loc1.radius, loc2.radius):
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


def remove_outdated(state: State, days_valid: int) -> Update:
    '''Update a state by removing localities that are outdated, determined
    by checking if the last activity within a given locality was at least
    some number of days ago.
    '''

    now = toUTC(datetime.now())
    last_valid_date = now - timedelta(days=days_valid)

    new_localities = [
        loc
        for loc in state.localities
        if loc.lastaction >= last_valid_date
    ]

    return Update(
        state=State.new(state.username, new_localities),
        did_update=len(new_localities) != len(state.localities))


def distance(loc1: Coordinates, loc2: Coordinates) -> float:
    '''Compute the distance between two points on the Earth, returning the
    geographical distance in kilometres (KM).
    '''

    lat1 = math.radians(loc1.latitude)
    lat2 = math.radians(loc2.latitude)
    lon1 = math.radians(loc1.longitude)
    lon2 = math.radians(loc2.longitude)

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = math.sin(dlat / 2.0) ** 2 +\
        math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2.0) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return c * _EARTH_RADIUS


def _coordinates(loc: Locality) -> Coordinates:
    return Coordinates(loc.latitude, loc.longitude)
