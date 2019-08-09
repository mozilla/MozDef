from datetime import datetime
from operator import attrgetter
from typing import List, NamedTuple, Optional

import netaddr

from alerts.geomodel.config import Whitelist
from alerts.geomodel.locality import State, Locality


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
            type_='geomodel',
            username=username,
            sourceipaddress=sourceip,
            timestamp=datetime.now(),
            origin=origin,
            tags=['geomodel'],
            summary=summary)

def _travel_possible(loc1: Locality, loc2: Locality) -> bool:
    '''Given two localities, determine whether it would be possible for a user
    to have travelled from the former to the latter in the time between when the
    actions took place.
    '''

    return False

def alert(user_state: State, whitelist: Whitelist) -> Optional[Alert]:
    '''Determine whether an alert should fired given a particular user's
    locality state.  If an alert should fire, an `Alert` is returned, otherwise
    this function returns `None`.
    '''

    ignore_cidrs = [netaddr.IPSet([cidr]) for cidr in whitelist.cidrs]

    if user_state.username in whitelist.users:
        return None

    locs_to_consider = []
    for loc in sorted(user_state.localities, key=attrgetter('lastaction')):
        ip = netaddr.IPAddress(loc.sourceipaddress)

        if all([ip not in cidr for cidr in ignore_cidrs]):
            locs_to_consider.append(loc)

    if len(locs_to_consider) < 2:
        return None

    locations = locs_to_consider[-2:]

    if _travel_possible(*locations):
        return None

    (ip, city, country, lat, lon) = (
        locations[1].sourceipaddress,
        locations[1].city,
        locations[1].country,
        locations[1].latitude,
        locations[1].longitude
    )

    return Alert.new(
        user_state.username,
        ip,
        Origin(city, country, lat, lon, ''))

