from functools import reduce
import sys
from typing import Any, Dict, List, NamedTuple

from mozdef_util.query_models import \
        QueryStringMatch as QSMatch, \
        SearchQuery

import config
import query


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
        search.add_must([QSMatch(cfg.lucene)])

        search_results = query_es(search, evt_cfg.es_index)

        for result in search_results:
            username = _lookup_path(result, cfg.username)

            events.append(QueryResult(username, result))

    return events
