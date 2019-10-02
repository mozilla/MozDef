import math
from operator import attrgetter
from typing import List, NamedTuple, Optional

from .locality import Locality, distance as geo_distance


_AIR_TRAVEL_SPEED = 277.778  # m/s

# TODO: Switch to dataclasses when we move to Python3.7+


class Origin(NamedTuple):
    '''A description of a location.
    '''

    ip: str
    city: str
    country: str
    latitude: float
    longitude: float
    geopoint: str


class Hop(NamedTuple):
    '''Describes a hop from one location to another that would be
    physically impossible in the time between a user's activity in each
    location.
    '''

    origin: Origin
    destination: Origin


class Alert(NamedTuple):
    '''A container for the data the alerts output by GeoModel contain.
    '''

    username: str
    hops: List[Hop]


def _travel_possible(loc1: Locality, loc2: Locality) -> bool:
    '''Given two localities, determine whether it would be possible for a user
    to have travelled from the former to the latter in the time between when the
    actions took place.
    '''

    dist_traveled = 1000 * geo_distance(loc1, loc2)  # Convert to metres

    seconds_between = abs((loc2.lastaction - loc1.lastaction).total_seconds())

    # We pad the time with an hour to account for things like planes being
    # slowed, network delays, etc.
    ttt = (dist_traveled / _AIR_TRAVEL_SPEED)  # Time to travel the distance.
    pad = math.ceil((1000 * min(loc1.radius, loc2.radius)) / _AIR_TRAVEL_SPEED)

    return (ttt - pad) <= seconds_between


def alert(
        username: str,
        from_evts: List[Locality],
        from_es: List[Locality]
) -> Optional[Alert]:
    '''Determine whether an alert should fire given a particular user's
    locality state.  If an alert should fire, an `Alert` is returned, otherwise
    this function returns `None`.
    '''

    relevant_es = sorted(from_es, key=attrgetter('lastaction'), reverse=True)[0:1]
    all_evts = sorted(from_evts, key=attrgetter('lastaction'))
    locs_to_consider = relevant_es + all_evts

    if len(locs_to_consider) < 2:
        return None

    pairs = [
        (locs_to_consider[i], locs_to_consider[i + 1])
        for i in range(len(locs_to_consider) - 1)
    ]

    hops = [
        Hop(
            Origin(
                o.sourceipaddress,
                o.city,
                o.country,
                o.latitude,
                o.longitude,
                '{},{}'.format(o.latitude, o.longitude)),
            Origin(
                d.sourceipaddress,
                d.city,
                d.country,
                d.latitude,
                d.longitude,
                '{},{}'.format(d.latitude, d.longitude)))
        for (o, d) in pairs
        if not _travel_possible(o, d)
    ]

    if len(hops) == 0:
        return None

    return Alert(username, hops)
