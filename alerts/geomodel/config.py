from typing import List, NamedTuple


# TODO: Switch to dataclasses when we move to Python3.7+


class Localities(NamedTuple):
    '''Contains configuration for working with locality state.
    '''

    es_index: str
    valid_duration_days: int
    radius_kilometres: float


class QuerySpec(NamedTuple):
    '''Contains a description of a query to run to retrieve specific events
    as well as a dot-string path (e.g. `"hello.world"`) into an event used to
    retrieve a username from the events returned by the aforementioned query.
    '''

    lucene: str
    username: str


class SearchWindow(NamedTuple):
    '''Contains parameters that specify the window of time to search for
    events in.
    '''

    minutes: int


class Events(NamedTuple):
    '''Contains configuration required to query for events in ElasticSearch.
    '''

    es_index: str
    search_window: SearchWindow
    queries: List[QuerySpec]


class Whitelist(NamedTuple):
    '''Specifies configuration for whitelisting rules.
    Any events created for any of the listed `users` will not be used in
    decision-making about generating alerts.
    Any events describing activity originating from an IP address in any
    of the list of CIDRs will also not be included in decision-making.
    '''

    users: List[str]
    cidrs: List[str]


class Alerts(NamedTuple):
    '''Contains configuration required to generate and store alerts in
    ElasticSearch.
    '''

    es_index: str
    whitelist: Whitelist


class Config(NamedTuple):
    '''The top-level configuration type.
    '''

    elasticsearch_address: str
    localities: Localities
    events: Events
    alerts: Alerts
