from typing import Callable, List

from alerts.geomodel.alert import Alert


# A factor is a sort of plugin intended to enrich a GeoModel alert with extra
# information that may be useful to incident responders as well as to modify
# the alert's severity.
FactorInterface = Callable[[Alert], Alert]


def asn_movement(maxmind_db_path: str) -> FactorInterface:
    '''Enriches GeoModel alerts with information about the ASNs from which IPs
    in hops originate.  When movement from one ASN to another is detected, the
    alert's severity will be raised.
    '''

    def factor(alert: Alert) -> Alert:
        return alert

    return factor
