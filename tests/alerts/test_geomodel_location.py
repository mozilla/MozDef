from datetime import datetime, timedelta

from freezegun import freeze_time

from mozdef_util.utilities.toUTC import toUTC

from tests.alerts.alert_test_suite import AlertTestSuite
from tests.alerts.negative_alert_test_case import NegativeAlertTestCase
from tests.alerts.positive_alert_test_case import PositiveAlertTestCase

import alerts.geomodel.locality as geomodel


class TestAlertGeoModel(AlertTestSuite):
    alert_filename = 'geomodel_location'

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
            'details': {
                'sourceipaddress': '1.2.3.4',
                'sourceipgeolocation': {
                    'city': 'Toronto',
                    'country_code': 'CA',
                    'latitude': 43.6529,
                    'longitude': -79.3849
                },
                'username': 'tester1'
            },
            'tags': ['auth0']
        }
    }

    no_change_event = {
        '_source': {
            'details': {
                'sourceipaddress': '4.3.2.1',
                'sourceipgeolocation': {
                    'city': 'Toronto',
                    'country_code': 'CA',
                    'latitude': 43.6529,
                    'longitude': -79.3849
                },
                'username': 'tester2'
            }
        }
    }

    default_alert = {
        'category': 'geomodel',
        'summary': 'tester1 is now active in Toronto,CA. Previously San Francisco,US',
        'details': {
            'username': 'tester1',
            'sourceipaddress': '1.2.3.4',
            'origin': {
                'city': 'Toronto',
                'country': 'CA',
                'latitude': 43.6529,
                'longitude': -79.3849,
                'geopoint': '43.6529,-79.3849'
            }
        },
        'severity': 'INFO',
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

    @freeze_time("2017-01-01 01:00:00", tz_offset=0)
    def setup(self):
        super().setup()

        index = 'localities'
        if self.config_delete_indexes:
            self.es_client.delete_index(index, True)
            self.es_client.create_index(index)

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
                    'lastaction': toUTC(datetime.now()) - timedelta(minutes=16),
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
                    'lastaction': toUTC(datetime.now()) - timedelta(hours=50),
                    'latitude': 43.6529,
                    'longitude': -79.3849,
                    'radius': 50
                })
            ])
        ]

        for state in test_states:
            journal(geomodel.Entry.new(state), index)

        self.refresh(index)

    def teardown(self):
        if self.config_delete_indexes:
            self.es_client.delete_index('localities', True)
        super().teardown()


class TestUpdateOrdering(AlertTestSuite):
    '''Alerts will trigger unexpectedly if locality state updates are applied
    before determining whether a user's location has changed by comparing
    localities from events against those in a recorded state.
    '''

    alert_filename = 'geomodel_location'
    alert_classname = "AlertGeoModel"

    default_event = {
        "_source": {
            "details": {
                "sourceipaddress": "1.2.3.4",
                "username": "tester1",
                "sourceipgeolocation": {
                    "city": "San Francisco",
                    "country_code": "US",
                    'latitude': 37.773972,
                    'longitude': -122.431297,
                },
            },
            "tags": ["auth0"],
        }
    }

    test_cases = [
        NegativeAlertTestCase(
            description='Alert should not fire if new city is most recent',
            events=[default_event])
    ]

    @freeze_time("2017-01-01 01:00:00", tz_offset=0)
    def setup(self):
        super().setup()

        index = 'localities'
        if self.config_delete_indexes:
            self.es_client.delete_index(index, True)
            self.es_client.create_index(index)

        journal = geomodel.wrap_journal(self.es_client)

        def state(username, locs):
            return geomodel.State('locality', username, locs)

        def locality(cfg):
            return geomodel.Locality(**cfg)

        test_states = [
            state('tester1', [
                locality({
                    'sourceipaddress': '1.2.3.4',
                    'city': 'San Francisco',
                    'country': 'US',
                    'lastaction': toUTC(datetime.now()) - timedelta(minutes=3),
                    'latitude': 37.773972,
                    'longitude': -122.431297,
                    'radius': 50
                }),
                locality({
                    'sourceipaddress': '9.8.7.6',
                    'city': 'Toronto',
                    'country': 'CA',
                    'lastaction': toUTC(datetime.now()) - timedelta(minutes=5),
                    'latitude': 43.6529,
                    'longitude': -79.3849,
                    'radius': 50
                })
            ])
        ]

        for state in test_states:
            journal(geomodel.Entry.new(state), index)
        self.refresh(index)

    def teardown(self):
        if self.config_delete_indexes:
            self.es_client.delete_index('localities', True)
        super().teardown()


class TestOnePreviousLocality(AlertTestSuite):
    alert_filename = 'geomodel_location'
    alert_classname = "AlertGeoModel"

    default_event = {
        "_source": {
            "details": {
                "sourceipaddress": "1.2.3.4",
                "username": "tester1",
                "sourceipgeolocation": {
                    "city": "San Francisco",
                    "country_code": "US",
                    'latitude': 37.773972,
                    'longitude': -122.431297,
                },
            },
            "tags": ["auth0"],
        }
    }

    default_alert = {
        'category': 'geomodel',
        'summary': 'tester1 is now active in San Francisco,US. Previously Toronto,CA',
        'details': {
            'username': 'tester1',
            'sourceipaddress': '1.2.3.4',
            'origin': {
                'city': 'San Francisco',
                'country': 'US',
                'latitude': 37.773972,
                'longitude': -122.431297,
                'geopoint': '37.773972,-122.431297'
            }
        },
        'severity': 'INFO',
        'tags': ['geomodel']
    }

    test_cases = [
        PositiveAlertTestCase(
            description='Alert fires with one previous locality state',
            events=[default_event],
            expected_alert=default_alert)
    ]

    @freeze_time("2017-01-01 01:00:00", tz_offset=0)
    def setup(self):
        super().setup()

        index = 'localities'
        if self.config_delete_indexes:
            self.es_client.delete_index(index, True)
            self.es_client.create_index(index)

        journal = geomodel.wrap_journal(self.es_client)

        def state(username, locs):
            return geomodel.State('locality', username, locs)

        def locality(cfg):
            return geomodel.Locality(**cfg)

        test_states = [
            state('tester1', [
                locality({
                    'sourceipaddress': '9.8.7.6',
                    'city': 'Toronto',
                    'country': 'CA',
                    'lastaction': toUTC(datetime.now()) - timedelta(minutes=5),
                    'latitude': 43.6529,
                    'longitude': -79.3849,
                    'radius': 50
                })
            ])
        ]

        for state in test_states:
            journal(geomodel.Entry.new(state), index)
        self.refresh(index)

    def teardown(self):
        if self.config_delete_indexes:
            self.es_client.delete_index('localities', True)
        super().teardown()


class TestInitialLocalityPositiveAlert(AlertTestSuite):
    alert_filename = 'geomodel_location'
    alert_classname = "AlertGeoModel"

    default_event = {
        "_source": {
            "details": {
                "sourceipaddress": "5.6.7.8",
                "username": "tester1",
                "sourceipgeolocation": {
                    "city": "Toronto",
                    "country_code": "CA",
                    'latitude': 43.6529,
                    'longitude': -79.3849,
                },
            },
            "tags": ["auth0"],
        }
    }

    default_alert = {
        'category': 'geomodel',
        'summary': 'tester1 is now active in Toronto,CA. Previously San Francisco,US',
        'details': {
            'username': 'tester1',
            'sourceipaddress': '5.6.7.8',
            'origin': {
                'city': 'Toronto',
                'country': 'CA',
                'latitude': 43.6529,
                'longitude': -79.3849,
                'geopoint': '43.6529,-79.3849'
            }
        },
        'severity': 'INFO',
        'tags': ['geomodel']
    }

    test_cases = [
        PositiveAlertTestCase(
            description='Alert fires when flipping between original and new locality',
            events=[default_event],
            expected_alert=default_alert),
    ]

    @freeze_time("2017-01-01 01:00:00", tz_offset=0)
    def setup(self):
        super().setup()

        index = 'localities'
        if self.config_delete_indexes:
            self.es_client.delete_index(index, True)
            self.es_client.create_index(index)

        journal = geomodel.wrap_journal(self.es_client)

        def state(username, locs):
            return geomodel.State('locality', username, locs)

        def locality(cfg):
            return geomodel.Locality(**cfg)

        test_states = [
            state('tester1', [
                locality({
                    'sourceipaddress': '1.2.3.4',
                    'city': 'San Francisco',
                    'country': 'US',
                    'lastaction': toUTC(datetime.now()) - timedelta(minutes=3),
                    'latitude': 37.773972,
                    'longitude': -122.431297,
                    'radius': 50
                }),
                locality({
                    'sourceipaddress': '9.8.7.6',
                    'city': 'Toronto',
                    'country': 'CA',
                    'lastaction': toUTC(datetime.now()) - timedelta(minutes=5),
                    'latitude': 43.6529,
                    'longitude': -79.3849,
                    'radius': 50
                })
            ])
        ]

        for state in test_states:
            journal(geomodel.Entry.new(state), index)
        self.refresh(index)

    def teardown(self):
        if self.config_delete_indexes:
            self.es_client.delete_index('localities', True)
        super().teardown()


class TestSameCitiesOutsideRange(AlertTestSuite):
    alert_filename = 'geomodel_location'
    alert_classname = "AlertGeoModel"

    default_event = {
        '_source': {
            'details': {
                'sourceipaddress': '1.2.3.4',
                'sourceipgeolocation': {
                    'city': 'Sherbrooke',
                    'country_code': 'CA',
                    'latitude': 45.3397,
                    'longitude': -72.013
                },
                'username': 'tester1'
            },
            'tags': ['auth0']
        }
    }
    same_city_event = {
        '_source': {
            'details': {
                'sourceipaddress': '5.6.7.8',
                'sourceipgeolocation': {
                    'city': 'Sherbrooke',
                    'country_code': 'CA',
                    'latitude': 45.3879,
                    'longitude': -71.8988
                },
                'username': 'tester1'
            },
            'tags': ['auth0']
        }
    }

    default_alert = {
        'category': 'geomodel',
        'summary': 'tester1 is now active in Sherbrooke,CA. Previously Sherbrooke,CA',
        'details': {
            'username': 'tester1',
            'sourceipaddress': '5.6.7.8',
            'origin': {
                'city': 'Sherbrooke',
                'country': 'CA',
                'latitude': 45.3879,
                'longitude': -71.8988,
                'geopoint': '45.3879,-71.8988'
            }
        },
        'severity': 'INFO',
        'tags': ['geomodel']
    }

    events = [
        AlertTestSuite.create_event(default_event),
        AlertTestSuite.create_event(same_city_event)
    ]
    test_cases = [
        PositiveAlertTestCase(
            description='Alert fires if cities are same but geopoints are outside range',
            events=events,
            expected_alert=default_alert),
    ]

    @freeze_time("2017-01-01 01:00:00", tz_offset=0)
    def setup(self):
        super().setup()

        index = 'localities'
        if self.config_delete_indexes:
            self.es_client.delete_index(index, True)
            self.es_client.create_index(index)

    def teardown(self):
        if self.config_delete_indexes:
            self.es_client.delete_index('localities', True)
        super().teardown()
