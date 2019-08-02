from datetime import datetime
from functools import reduce
from typing import Any, Dict, List, NamedTuple, Optional

from mozdef_util.query_models import\
    QueryStringMatch as QSMatch,\
    SearchQuery

import alerts.geomodel.config as config
from alerts.geomodel.locality import Locality
import alerts.geomodel.query as query


# Default radius (in Kilometres) that a locality should have.
_DEFAULT_RADIUS_KM = 50.0


def _lookup_path(nested_dict, dot_key):
    return reduce(
        lambda d, k: d.get(k) if d is not None else None,
        dot_key.split('.'),
        nested_dict)


# TODO: Replace with a dataclass when we move to Python 3.7+
class QueryResult(NamedTuple):
    '''A container for the data extracted from ElasticSearch by a call to
    `find_all`.
    '''

    username: str
    event: Dict[str, Any]


def find_all(
        query_es: query.QueryInterface,
        evt_cfg: config.Events
) -> List[QueryResult]:
    '''Retrieve events from ElasticSearch produced by running the set of
    queries Geoodel has been configured with.
    '''

    events = []

    for cfg in evt_cfg.queries:
        search = SearchQuery(minutes=evt_cfg.search_window.minutes)
        search.add_must(QSMatch(cfg.lucene))

        search_results = query_es(search, evt_cfg.es_index)

        for result in search_results:
            username = _lookup_path(result, cfg.username)

            events.append(QueryResult(username, result))

    return events


def extract_locality(
        event: Dict[str, Any],
        radius=_DEFAULT_RADIUS_KM
) -> Optional[Locality]:
    '''Extract information about the `sourceipaddress` from which a user's
    event-triggering action was taken along with other locality data if it
    is present.
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
