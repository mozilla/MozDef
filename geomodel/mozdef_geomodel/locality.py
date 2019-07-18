from mozdef_util.query_models import SearchQuery, TermMatch

import config
import query


def find_all(
        query_es: query.QueryInterface,
        locality: config.Localities
        ) -> List[query.Event]:
    '''Retrieve all locality state from ElasticSearch.
    '''

    search = SearchQuery()
    search.add_must([TermMatch('type', 'locality')])

    return query_es(search, locality.esindex)
