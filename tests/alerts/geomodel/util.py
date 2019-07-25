from typing import Any, Dict, List

from mozdef_util.query_models import SearchQuery

import alerts.geomodel.query as query


def query_interface(results: List[Dict[str, Any]]) -> query.QueryInterface:
    '''Produce a `QueryInterface` that just returns the provided results.
    '''

    def closure(q: SearchQuery, esi: str) -> List[Dict[str, Any]]:
        return results

    return closure
