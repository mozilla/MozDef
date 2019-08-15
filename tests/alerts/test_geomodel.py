from tests.alerts.alert_test_suite import AlertTestSuite
from tests.alerts.negative_alert_test_case import NegativeAlertTestCase
from tests.alerts.positive_alert_test_case import PositiveAlertTestCase


class TestAlertGeoModel(AlertTestSuite):
    alert_filename = 'geomodel'

    default_event = {
        '_source': {
            'sourceipaddress': '1.2.3.4',
            'sourceipgeolocation': {
                'city': 'Toronto',
                'country_code': 'CA',
                'latitude': 43.6529,
                'longitude': -79.3849
            },
            'details': {
                'username': 'tester'
            }
        }
    }
    
    no_change_event = {
        '_source': {
            'sourceipaddress': '1.2.3.4',
            'sourceipgeolocation': {
                'city': 'Toronto',
                'country_code': 'CA',
                'latitude': 43.6529,
                'longitude': -79.3849
            },
            'details': {
                'username': 'tester2'
            }
        }
    }

    default_alert = {
        'source': 'geomodel',
        'category': 'geomodel',
        'type_': 'geomodel',
        'username': 'tester',
        'sourceipaddress': '1.2.3.4',
        'timestamp': '2019-07-31T17:56:38.908000+00:00',
        'origin': {
            'city': 'Toronto',
            'country': 'CA',
            'latitude': 43.6529,
            'longitude': -79.3849
        },
        'tags': ['geomodel'],
        'summary': 'Authenticated action taken by a user outside of any of '\
            'their known localities.'
    }

    test_cases = [
        PositiveAlertTestCase(
            description='Alert fires when impossible travel between two '\
                'localities detected',
            events=[default_event],
            expected_alert=default_alert),
        NegativeAlertTestCase(
            description='Alert does not fire if locality did not change',
            events=[no_change_event])
    ]

    def setup(self):
        super().setup()
