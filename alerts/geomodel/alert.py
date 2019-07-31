from datetime import datetime
from typing import List, NamedTuple


_DEFAULT_SUMMARY = 'Authenticated action taken by a user outside of any of '\
    'their known localities.'

# TODO: Switch to dataclasses when we move to Python3.7+


class Origin(NamedTuple):
    '''A description of a location.
    '''

    city: str
    country: str
    latitude: float
    longitude: float
    geopoint: str


class Alert(NamedTuple):
    '''A container for the data the alerts output by GeoModel contain.
    '''

    source: str
    category: str
    type_: str
    username: str
    sourceipaddress: str
    timestamp: datetime
    origin: Origin
    tags: List[str]
    summary: str

    def new(
        username: str,
        sourceip: str,
        origin: Origin,
        summary: str = _DEFAULT_SUMMARY
    ) -> 'Alert':
        '''Produce a new `Alert` with default values filled.
        '''

        return Alert(
            source='geomodel',
            category='geomodel',
            _type='geomodel',
            username=username,
            sourceipaddress=sourceip,
            timestamp=datetime.now(),
            origin=origin,
            tags=['geomodel'],
            summary=summary)
