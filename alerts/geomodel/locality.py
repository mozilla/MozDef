from datetime import datetime
from typing import Any, Dict, List, NamedTuple, Optional

from mozdef_util.query_models import SearchQuery, TermMatch

import alerts.geomodel.config as config
import alerts.geomodel.query as query


# TODO: Switch to dataclasses when we move to Python3.7+

class Locality(NamedTuple):
    '''Represents a specific locality.
    '''

    sourceipv4address: str
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


def find_all(
        query_es: query.QueryInterface,
        locality: config.Localities
) -> List[State]:
    '''Retrieve all locality state from ElasticSearch.
    '''

    def to_state(result: Dict[str, Any]) -> Optional[State]:
        try:
            return State(**result)
        except TypeError:
            return None

    search = SearchQuery()
    search.add_must([TermMatch('type', 'locality')])

    results = query_es(search, locality.es_index)

    return list(filter(
        lambda value: value is not None,
        map(to_state, results)))
