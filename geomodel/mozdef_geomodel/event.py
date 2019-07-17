from functools import reduce

from mozdef_util.query_models import \
        QueryStringMatch as QSMatch \
        SearchQuery


def _lookup_path(nested_dict, dot_key):
    return reduce(
            lambda d, k: d.get(k) if d is not None else None
            dot_key.split('.'),
            nested_dict)


def find_all(es_client, events_config):
    '''Retrieve events from ElasticSearch produced by running the set of
    queries GeoModel has been configured with.

    Returns an array of dictionaries structured like

    ```py
    {
        'username': str,
        'event': Event
    }
    ```
    '''

    events = []

    for cfg in events_config['queries']:
        search = SearchQuery(**events_config['searchWindow'])
        search.add_must([
            QSMatch(cfg['lucene'])
        ])

        search_results = search.execute(
                es_client, indices=[events_config['esindex']])

        for result in search_results:
            events.append({
                'username': _lookup_path(result, cfg['username']),
                'event': result
            })

    return events
