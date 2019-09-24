import math
from operator import attrgetter
from typing import List, NamedTuple, Optional

from .locality import Locality, distance as geo_distance


_AIR_TRAVEL_SPEED = 277.778  # m/s

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

    dist_traveled = 1000 * geo_distance(loc1, loc2)  # Convert to metres

    seconds_between = (loc2.lastaction - loc1.lastaction).total_seconds()

    # We pad the time with an hour to account for things like planes being
    # slowed, network delays, etc.
    ttt = (dist_traveled / _AIR_TRAVEL_SPEED)  # Time to travel the distance.
    pad = math.ceil((1000 * min(loc1.radius, loc2.radius)) / _AIR_TRAVEL_SPEED)
    return seconds_between <= (ttt + pad)


def alert(username: str, locs: List[Locality]) -> Optional[Alert]:
    '''Determine whether an alert should fire given a particular user's
    locality state.  If an alert should fire, an `Alert` is returned, otherwise
    this function returns `None`.
    '''

    locs_to_consider = sorted(locs, key=attrgetter('lastaction'))

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

    return Alert(username, ip, origin)
