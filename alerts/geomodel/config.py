from typing import List, NamedTuple


# TODO: Switch to dataclasses when we move to Python3.7+

class Localities(NamedTuple):
    '''Contains configuration for working with locality state.
    '''

    es_index: str
    valid_duration_days: int
    radius_kilometres: float


class Events(NamedTuple):
    '''Contains configuration required to query for events in ElasticSearch.
    '''

    search_window: dict
    lucene_query: str


class Whitelist(NamedTuple):
    '''Specifies configuration for whitelisting rules.
    Any events created for any of the listed `users` will not be used in
    decision-making about generating alerts.
    Any events describing activity originating from an IP address in any
    of the list of CIDRs will also not be included in decision-making.
    '''

    users: List[str]
    cidrs: List[str]


class ASNMovement(NamedTuple):
    '''Configuration for the `asn_movement` factor.
    '''

    maxmind_db_path: str


class Factors(NamedTuple):
    '''Configuration for factors.
    '''

    asn_movement: ASNMovement


class Config(NamedTuple):
    '''The top-level configuration type.
    '''

    asn_movement_severity: str
    severity: str
    localities: Localities
    events: Events
    whitelist: Whitelist
    factors: Factors
