from functools import reduce
from typing import Any, Dict, NamedTuple

from mozdef_util.query_models import \
        QueryStringMatch as QSMatch \
        SearchQuery

import config
import query


def _lookup_path(nested_dict, dot_key):
    return reduce(
            lambda d, k: d.get(k) if d is not None else None
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
        events: config.Events
        ) -> List[QueryResult]:
    '''Retrieve events from ElasticSearch produced by running the set of
    queries GeoModel has been configured with.
    '''

    events = []

    for cfg in events_config['queries']:
        search = SearchQuery(**events_config.search_window)
        search.add_must([QSMatch(cfg.lucene)])

        search_results = query_es(search, events.esindex)

        for result in search_results:
            username = _lookup_path(result, cfg.username)

            events.append(QueryResult(username, result))

    return events
