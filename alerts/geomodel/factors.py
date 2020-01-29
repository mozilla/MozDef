from typing import Callable, List
from functools import reduce

import maxminddb as mmdb

from alerts.geomodel.alert import Alert, Severity


# A factor is a sort of plugin intended to enrich a GeoModel alert with extra
# information that may be useful to incident responders as well as to modify
# the alert's severity.
FactorInterface = Callable[[Alert], Alert]


def pipe(alert: Alert, factors: List[FactorInterface]) -> Alert:
    '''Run an alert through an ordered pipeline of factors.
    '''

    return reduce(
        lambda a, fn: fn(a),
        factors,
        alert)


def asn_movement(maxmind_db_path: str, escalate: Severity) -> FactorInterface:
    '''Enriches GeoModel alerts with information about the ASNs from which IPs
    in hops originate.  When movement from one ASN to another is detected, the
    alert's severity will be raised.

    `maxmind_db_path` is the path to a MaxMind database file containing
    information about ASNs.

    `escalate` is the severity to (de-)escalate the alert to/from in the case
    that movement from one ASN to another is detected in the alert.
    '''
        
    # Keys in the dictionaries returned by MaxMind.
    asn = 'autonomous_system_number'
    org = 'autonomous_system_organization'

    def factor(alert: Alert) -> Alert:
        # We want to manage the "connection" to the maxminddb correctly,
        # closing it when we're finished. Since opening a connection isn't
        # expensive, we prefer not to delegate handling the dependency to
        # the GeoModel alert itself.
        db = mmdb.open_database(maxmind_db_path)

        ips = [hop.origin.ip for hop in alert.hops]
        if len(alert.hops) > 0:
            ips.append(alert.hops[-1].destination.ip)

        unique_ips = list(set(ips))

        asn_info = [db.get(ip) for ip in unique_ips]
        asn_pairs = [
            (asn_info[i], asn_info[i + 1])
            for i in range(len(asn_info) - 1)
        ]
        asn_hops = [
            pair
            for pair in asn_pairs
            if pair[0][org] != pair[1][org]
        ]

        alert.factors.append({
            'asn_hops': asn_hops
        })

        if len(asn_hops) > 0:
            alert.severity = escalate

        db.close()

        return alert

    return factor
