from datetime import datetime
import math
from operator import attrgetter
from typing import List, NamedTuple, Optional

from .locality import Coordinates, Locality, distance as geo_distance


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
    observed: datetime
    geopoint: str


class Hop(NamedTuple):
    '''Describes a hop from one location to another that would be
    physically impossible in the time between a user's activity in each
    location.
    '''

    origin: Origin
    destination: Origin

    def to_json(self):
        '''Convert a `Hop` to a fully JSON (`dict`) representation.
        '''

        return {
            'origin': dict(self.origin._asdict()),
            'destination': dict(self.destination._asdict()),
        }


class Alert(NamedTuple):
    '''A container for the data the alerts output by GeoModel contain.

    '''

    username: str
    hops: List[Hop]
    severity: str
    # Because we cannot know ahead of time what factors (see factors.py) will
    # have been implemented and registered for use, this container should be
    # thought of as something of a black-box useful only for humans looking
    # at the alert after it fires.
    factors: List[dict]


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
        from_es: List[Locality],
        severity: str
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
        Hop(_to_origin(o), _to_origin(d))
        for (o, d) in pairs
        if not _travel_possible(o, d)
    ]

    if len(hops) == 0:
        return None

    return Alert(username, hops, severity, [])


def summary(alert: Alert) -> str:
    '''Produces a human-readable summary of the 'hops' between locations
    described in an alert.
    '''

    _d = [
        geo_distance(_coordinates(hop.origin), _coordinates(hop.destination))
        for hop in alert.hops
    ]

    dists = ['{:.2f} KM'.format(d) for d in _d]

    _t = [
        (hop.origin.observed - hop.destination.observed).total_seconds()
        for hop in alert.hops
    ]

    times = ['{:.2f} minutes'.format(abs(t) / 60.0) for t in _t]

    hops = [
        '{},{} then {},{} ({} in {})'.format(
            alert.hops[i].origin.city,
            alert.hops[i].origin.country,
            alert.hops[i].destination.city,
            alert.hops[i].destination.country,
            dists[i],
            times[i])
        for i in range(len(alert.hops))
    ]

    return '{} seen in {}'.format(alert.username, '; '.join(hops))


def _coordinates(orig: Origin) -> Coordinates:
    return Coordinates(orig.latitude, orig.longitude)


def _to_origin(loc: Locality) -> Origin:
    return Origin(
        loc.sourceipaddress,
        loc.city,
        loc.country,
        loc.latitude,
        loc.longitude,
        loc.lastaction,
        '{},{}'.format(loc.latitude, loc.longitude))
