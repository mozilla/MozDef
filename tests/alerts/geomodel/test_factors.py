from datetime import datetime

import alerts.geomodel.alert as alert
import alerts.geomodel.factors as factors


class MockMMDB:
    '''Mocks a MaxMind database connection with a dictionary of records mapping
    IP adresses to dictionaries containing information about ASNs.
    '''

    def __init__(self, records):
        self.records = records

    def get(self, ip):
        return self.records.get(ip)

    def close(self):
        return


def null_origin(ip):
    return alert.Origin(
        ip=ip,
        city='Null',
        country='NA',
        latitude=0.0,
        longitude=0.0,
        observed=datetime.now(),
        geopoint='0.0,0.0')


# A set of records for a mocked MaxMind database containing information about
# ASNs used to test the `asn_movement` factor implementation with.
asn_mvmt_records = {
    '1.2.3.4': {
        'autonomous_system_number': 54321,
        'autonomous_system_organization': 'CLOUDFLARENET'
    },
    '4.3.2.1': {
        'autonomous_system_number': 12345,
        'autonomous_system_organization': 'MOZILLA_SFO1'
    },
    '5.6.7.8': {
        'autonomous_system_number': 67891,
        'autonomous_system_organization': 'AMAZONAWSNET'
    }
}


def test_asn_movement():
    factor = factors.asn_movement(
        MockMMDB(asn_mvmt_records),
        'WARNING')

    test_hops = [
        alert.Hop(
            origin=null_origin('1.2.3.4'),
            destination=null_origin('4.3.2.1')),
        alert.Hop(
            origin=null_origin('4.3.2.1'),
            destination=null_origin('5.6.7.8'))
    ]

    test_alert = alert.Alert(
        username='tester',
        hops=test_hops,
        severity='INFO',
        factors=[])

    pipeline = [factor]

    modified_alert = factors.pipe(test_alert, pipeline)

    assert modified_alert.username == test_alert.username
    assert modified_alert.severity == 'WARNING'
    assert len(modified_alert.factors) == 1
    assert 'asn_hops' in modified_alert.factors[0]
    assert len(modified_alert.factors[0]['asn_hops']) == 2

    asn_key = 'autonomous_system_organization'
    asn1 = modified_alert.factors[0]['asn_hops'][0][0][asn_key]
    asn2 = modified_alert.factors[0]['asn_hops'][0][1][asn_key]
    asn3 = modified_alert.factors[0]['asn_hops'][1][0][asn_key]
    asn4 = modified_alert.factors[0]['asn_hops'][1][1][asn_key]

    assert asn1 == 'CLOUDFLARENET'
    assert asn2 == 'MOZILLA_SFO1'
    assert asn3 == 'MOZILLA_SFO1'
    assert asn4 == 'AMAZONAWSNET'
