from typing import Callable, List, NamedTuple
from functools import reduce

from .alert import Alert


class Enhancement(NamedTuple):
    '''Information to enhance an `Alert` with, produced by an implementation of
    a `FactorInterface`.  The `pipe` function handles constructing a modified
    `Alert` with enhancements applied.
    '''

    extras: dict
    severity: str


# A factor is a sort of plugin intended to enrich a GeoModel alert with extra
# information that may be useful to incident responders as well as to modify
# the alert's severity.
FactorInterface = Callable[[Alert], Enhancement]


def pipe(alert: Alert, factors: List[FactorInterface]) -> Alert:
    '''Run an alert through an ordered pipeline of factors, applying the
    `Enhancement`s produced by each in turn.
    '''

    def _apply_enhancement(alert: Alert, enhance: Enhancement) -> Alert:
        return Alert(
            username=alert.username,
            hops=alert.hops,
            severity=enhance.severity,
            factors=alert.factors + [enhance.extras])

    return reduce(
        lambda alrt, fctr: _apply_enhancement(alrt, fctr(alrt)),
        factors,
        alert)


def asn_movement(db, escalate: str) -> FactorInterface:
    '''Enriches GeoModel alerts with information about the ASNs from which IPs
    in hops originate.  When movement from one ASN to another is detected, the
    alert's severity will be raised.

    `maxmind_db_path` is the path to a MaxMind database file containing
    information about ASNs.

    `escalate` is the severity to (de-)escalate the alert to/from in the case
    that movement from one ASN to another is detected in the alert.
    '''

    # Keys in the dictionaries returned by MaxMind.
    # asn = 'autonomous_system_number'  # currently not used
    org = 'autonomous_system_organization'

    def factor(alert: Alert) -> Enhancement:
        ips = [hop.origin.ip for hop in alert.hops]
        if len(alert.hops) > 0:
            ips.append(alert.hops[-1].destination.ip)

        # Converting the list of IPs to a set to get the unique items can
        # result in items being re-arranged.
        unique_ips = list({ip: True for ip in ips}.keys())

        asn_info = [db.get(ip) for ip in unique_ips]
        asn_pairs = [
            (asn_info[i], asn_info[i + 1])
            for i in range(len(asn_info) - 1)
            if asn_info[i] is not None and asn_info[i + 1] is not None
        ]
        asn_hops = [
            pair
            for pair in asn_pairs
            if pair[0][org] != pair[1][org]
        ]

        return Enhancement(
            extras={'asn_hops': asn_hops},
            severity=escalate if len(asn_hops) > 0 else alert.severity)

    return factor
