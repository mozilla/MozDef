from functools import reduce
from typing import Any, Dict, List, NamedTuple, Optional

from mozdef_util.query_models import\
    QueryStringMatch as QSMatch,\
    SearchQuery

import alerts.geomodel.config as config
import alerts.geomodel.query as query


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

        print(f'Constructed search query {search}')

        search_results = query_es(search, evt_cfg.es_index)

        print(f'Got search results {search_results}')
        for result in search_results:
            username = _lookup_path(result, cfg.username)

            events.append(QueryResult(username, result))

    return events


def extract_sourceip(event: Dict[str, Any]) -> Optional[str]:
    '''Search an event for a `sourceipaddress` field mapping to either an IPv4
    or IPv6 address.
    '''

    ip = event.get('sourceipaddress', None)

    if ip is not None:
        return ip

    for _key, value in event.items():
        # First try recursing into a dictionary.
        if isinstance(value, dict):
            ip = extract_sourceip(value)

            if ip is not None:
                return ip
            else:
                continue

        # Next check if we are looking at an array of dicts.
        is_valid_array = isinstance(value, list) and\
            all([isinstance(item, dict) for item in value])

        if is_valid_array:
            ips = list(filter(
                lambda ip: ip is not None,
                map(extract_sourceip, value)))

            if len(ips) > 0:
                return ips[0]
            else:
                continue

    # Did not find the key anywhere.
    return None
