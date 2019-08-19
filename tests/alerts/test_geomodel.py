from datetime import datetime, timedelta

from tests.alerts.alert_test_suite import AlertTestSuite
from tests.alerts.negative_alert_test_case import NegativeAlertTestCase
from tests.alerts.positive_alert_test_case import PositiveAlertTestCase

import alerts.geomodel.locality as geomodel


class TestAlertGeoModel(AlertTestSuite):
    alert_filename = 'geomodel_alert'

    # The test cases described herein depend on some locality state being
    # present before the tests run.
    # The state we set up establishes a locality in San Francisco for user
    # tester1 in which they were active a short period of time ago.  Another
    # state is established in Toronto for user tester2.
    # Given the states described above, detecting activity from tester1 in
    # Toronto is expected to trigger an alert since it is a new locality that
    # tester1 could not have travelled to.  On the other hand, no alert should
    # fire for tester2 since both localities are in Toronto.

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
                'username': 'tester1'
            },
            'tags': ['auth0']
        }
    }

    no_change_event = {
        '_source': {
            'sourceipaddress': '4.3.2.1',
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
        'username': 'tester1',
        'sourceipaddress': '1.2.3.4',
        'timestamp': '2019-07-31T17:56:38.908000+00:00',
        'origin': {
            'city': 'Toronto',
            'country': 'CA',
            'latitude': 43.6529,
            'longitude': -79.3849
        },
        'summary': 'Authenticated action taken by a user outside of any of '
        'their known localities.',
        'tags': ['geomodel']
    }

    test_cases = [
        PositiveAlertTestCase(
            description='Alert fires when impossible travel between two '
            'localities detected',
            events=[default_event],
            expected_alert=default_alert),
        NegativeAlertTestCase(
            description='Alert does not fire if locality did not change',
            events=[no_change_event])
    ]

    def setup(self):
        super().setup()

        self.es_client.delete_index('localities', True)
        self.es_client.create_index('localities')

        journal = geomodel.wrap_journal(self.es_client)

        def state(username, locs):
            return geomodel.State('locality', username, locs)

        def locality(cfg):
            return geomodel.Locality(**cfg)

        test_states = [
            state('tester1', [
                locality({
                    'sourceipaddress': '4.3.2.1',
                    'city': 'San Francisco',
                    'country': 'US',
                    'lastaction': datetime.utcnow() - timedelta(minutes=16),
                    'latitude': 37.773972,
                    'longitude': -122.431297,
                    'radius': 50
                })
            ]),
            state('tester2', [
                locality({
                    'sourceipaddress': '2.4.8.16',
                    'city': 'Toronto',
                    'country': 'CA',
                    'lastaction': datetime.utcnow() - timedelta(hours=50),
                    'latitude': 43.6529,
                    'longitude': -79.3849,
                    'radius': 50
                })
            ])
        ]

        for state in test_states:
            journal(geomodel.Entry.new(state), 'localities')

        self.refresh('localities')
