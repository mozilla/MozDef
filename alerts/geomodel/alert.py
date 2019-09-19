import math
from operator import attrgetter
from typing import NamedTuple, Optional

from .locality import State, Locality


_AIR_TRAVEL_SPEED = 1000.0  # km/h

_EARTH_RADIUS = 6373.0  # km # approximate

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

    username: str
    sourceipaddress: str
    origin: Origin


def _travel_possible(loc1: Locality, loc2: Locality) -> bool:
    '''Given two localities, determine whether it would be possible for a user
    to have travelled from the former to the latter in the time between when the
    actions took place.
    '''

    lat1 = math.radians(loc1.latitude)
    lat2 = math.radians(loc2.latitude)
    lon1 = math.radians(loc1.longitude)
    lon2 = math.radians(loc2.longitude)

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = math.sin(dlat / 2.0) ** 2 +\
        math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2.0) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    distance = c * _EARTH_RADIUS

    seconds_between = (loc2.lastaction - loc1.lastaction).total_seconds()
    hours_between = math.ceil(seconds_between / 60.0 / 60.0)

    # We pad the time with an hour to account for things like planes being
    # slowed, network delays, etc.
    return (distance / _AIR_TRAVEL_SPEED) <= (hours_between - 1)


def alert(user_state: State) -> Optional[Alert]:
    '''Determine whether an alert should fire given a particular user's
    locality state.  If an alert should fire, an `Alert` is returned, otherwise
    this function returns `None`.
    '''

    locs_to_consider = sorted(user_state.localities, key=attrgetter('lastaction'))

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

    geo = '{0},{1}'.format(lat, lon)
    origin = Origin(city, country, lat, lon, geo)

    return Alert(user_state.username, ip, origin)
