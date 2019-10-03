from datetime import datetime, timedelta

from freezegun import freeze_time

from mozdef_util.utilities.toUTC import toUTC

from tests.alerts.alert_test_suite import AlertTestSuite
from tests.alerts.negative_alert_test_case import NegativeAlertTestCase
from tests.alerts.positive_alert_test_case import PositiveAlertTestCase

import alerts.geomodel.locality as geomodel
import alerts.geomodel.execution as execution


def _summary_from_events(events):
    hops = ' then '.join(
        [
            '{0},{1}'.format(
                event['_source']['details']['sourceipgeolocation']['city'],
                event['_source']['details']['sourceipgeolocation']['country_code'],
            )
            for event in events
        ]
    )

    return '{0} seen in {1}'.format(events[0]['_source']['details']['username'], hops)


def _hops_from_events(events):
    details = [event['_source']['details'] for event in events]

    pairs = [(details[i], details[i + 1]) for i in range(len(details) - 1)]

    return [
        {
            'origin': {
                'ip': orig['sourceipaddress'],
                'city': orig['sourceipgeolocation']['city'],
                'country': orig['sourceipgeolocation']['country_code'],
                'latitude': orig['sourceipgeolocation']['latitude'],
                'longitude': orig['sourceipgeolocation']['longitude'],
                'geopoint': '{0},{1}'.format(
                    orig['sourceipgeolocation']['latitude'],
                    orig['sourceipgeolocation']['longitude'],
                ),
            },
            'destination': {
                'ip': dest['sourceipaddress'],
                'city': dest['sourceipgeolocation']['city'],
                'country': dest['sourceipgeolocation']['country_code'],
                'latitude': dest['sourceipgeolocation']['latitude'],
                'longitude': dest['sourceipgeolocation']['longitude'],
                'geopoint': '{0},{1}'.format(
                    dest['sourceipgeolocation']['latitude'],
                    dest['sourceipgeolocation']['longitude'],
                ),
            },
        }
        for (orig, dest) in pairs
    ]


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
                    'longitude': -79.3849,
                },
                'username': 'tester1',
            },
            'tags': ['auth0'],
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
                    'longitude': -79.3849,
                },
                'username': 'tester2',
            }
        }
    }

    default_alert = {
        'category': 'geomodel',
        'summary': 'tester1 seen in San Francisco,US then Toronto,CA',
        'details': {
            'username': 'tester1',
            'hops': [
                {
                    'origin': {
                        'ip': '4.3.2.1',
                        'city': 'San Francisco',
                        'country': 'US',
                        'latitude': 37.773972,
                        'longitude': -122.431297,
                        'geopoint': '37.773972,-122.431297',
                    },
                    'destination': {
                        'ip': '1.2.3.4',
                        'city': 'Toronto',
                        'country': 'CA',
                        'latitude': 43.6529,
                        'longitude': -79.3849,
                        'geopoint': '43.6529,-79.3849',
                    },
                }
            ],
        },
        'severity': 'INFO',
        'tags': ['geomodel'],
    }

    test_cases = [
        PositiveAlertTestCase(
            description='Alert fires when impossible travel between two '
            'localities detected',
            events=[default_event],
            expected_alert=default_alert,
        ),
        NegativeAlertTestCase(
            description='Alert does not fire if locality did not change',
            events=[no_change_event],
        ),
    ]

    @freeze_time('2017-01-01 01:00:00', tz_offset=0)
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
            state(
                'tester1',
                [
                    locality(
                        {
                            'sourceipaddress': '4.3.2.1',
                            'city': 'San Francisco',
                            'country': 'US',
                            'lastaction': toUTC(datetime.now()) - timedelta(minutes=16),
                            'latitude': 37.773972,
                            'longitude': -122.431297,
                            'radius': 50,
                        }
                    )
                ],
            ),
            state(
                'tester2',
                [
                    locality(
                        {
                            'sourceipaddress': '2.4.8.16',
                            'city': 'Toronto',
                            'country': 'CA',
                            'lastaction': toUTC(datetime.now()) - timedelta(hours=50),
                            'latitude': 43.6529,
                            'longitude': -79.3849,
                            'radius': 50,
                        }
                    )
                ],
            ),
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
    alert_classname = 'AlertGeoModel'

    default_event = {
        '_source': {
            'details': {
                'sourceipaddress': '1.2.3.4',
                'username': 'tester1',
                'sourceipgeolocation': {
                    'city': 'San Francisco',
                    'country_code': 'US',
                    'latitude': 37.773972,
                    'longitude': -122.431297,
                },
            },
            'tags': ['auth0'],
        }
    }

    test_cases = [
        NegativeAlertTestCase(
            description='Alert should not fire if new city is most recent',
            events=[default_event],
        )
    ]

    @freeze_time('2017-01-01 01:00:00', tz_offset=0)
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
            state(
                'tester1',
                [
                    locality(
                        {
                            'sourceipaddress': '1.2.3.4',
                            'city': 'San Francisco',
                            'country': 'US',
                            'lastaction': toUTC(datetime.now()) - timedelta(minutes=3),
                            'latitude': 37.773972,
                            'longitude': -122.431297,
                            'radius': 50,
                        }
                    ),
                    locality(
                        {
                            'sourceipaddress': '9.8.7.6',
                            'city': 'Toronto',
                            'country': 'CA',
                            'lastaction': toUTC(datetime.now()) - timedelta(minutes=5),
                            'latitude': 43.6529,
                            'longitude': -79.3849,
                            'radius': 50,
                        }
                    ),
                ],
            )
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
    alert_classname = 'AlertGeoModel'

    default_event = {
        '_source': {
            'details': {
                'sourceipaddress': '1.2.3.4',
                'username': 'tester1',
                'sourceipgeolocation': {
                    'city': 'San Francisco',
                    'country_code': 'US',
                    'latitude': 37.773972,
                    'longitude': -122.431297,
                },
            },
            'tags': ['auth0'],
        }
    }

    default_alert = {
        'category': 'geomodel',
        'summary': 'tester1 seen in Toronto,CA then San Francisco,US',
        'details': {
            'username': 'tester1',
            'hops': [
                {
                    'origin': {
                        'ip': '9.8.7.6',
                        'city': 'Toronto',
                        'country': 'CA',
                        'latitude': 43.6529,
                        'longitude': -79.3849,
                        'geopoint': '43.6529,-79.3849',
                    },
                    'destination': {
                        'ip': '1.2.3.4',
                        'city': 'San Francisco',
                        'country': 'US',
                        'latitude': 37.773972,
                        'longitude': -122.431297,
                        'geopoint': '37.773972,-122.431297',
                    },
                }
            ],
        },
        'severity': 'INFO',
        'tags': ['geomodel'],
    }

    test_cases = [
        PositiveAlertTestCase(
            description='Alert fires with one previous locality state',
            events=[default_event],
            expected_alert=default_alert,
        )
    ]

    @freeze_time('2017-01-01 01:00:00', tz_offset=0)
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
            state(
                'tester1',
                [
                    locality(
                        {
                            'sourceipaddress': '9.8.7.6',
                            'city': 'Toronto',
                            'country': 'CA',
                            'lastaction': toUTC(datetime.now()) - timedelta(minutes=5),
                            'latitude': 43.6529,
                            'longitude': -79.3849,
                            'radius': 50,
                        }
                    )
                ],
            )
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
    alert_classname = 'AlertGeoModel'

    default_event = {
        '_source': {
            'details': {
                'sourceipaddress': '5.6.7.8',
                'username': 'tester1',
                'sourceipgeolocation': {
                    'city': 'Toronto',
                    'country_code': 'CA',
                    'latitude': 43.6529,
                    'longitude': -79.3849,
                },
            },
            'tags': ['auth0'],
        }
    }

    default_alert = {
        'category': 'geomodel',
        'summary': 'tester1 seen in San Francisco,US then Toronto,CA',
        'details': {
            'username': 'tester1',
            'hops': [
                {
                    'origin': {
                        'ip': '1.2.3.4',
                        'city': 'San Francisco',
                        'country': 'US',
                        'latitude': 37.773972,
                        'longitude': -122.431297,
                        'geopoint': '37.773972,-122.431297',
                    },
                    'destination': {
                        'ip': '5.6.7.8',
                        'city': 'Toronto',
                        'country': 'CA',
                        'latitude': 43.6529,
                        'longitude': -79.3849,
                        'geopoint': '43.6529,-79.3849',
                    },
                }
            ],
        },
        'severity': 'INFO',
        'tags': ['geomodel'],
    }

    test_cases = [
        PositiveAlertTestCase(
            description='Alert fires when flipping between original and new locality',
            events=[default_event],
            expected_alert=default_alert,
        )
    ]

    @freeze_time('2017-01-01 01:00:00', tz_offset=0)
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
            state(
                'tester1',
                [
                    locality(
                        {
                            'sourceipaddress': '1.2.3.4',
                            'city': 'San Francisco',
                            'country': 'US',
                            'lastaction': toUTC(datetime.now()) - timedelta(minutes=3),
                            'latitude': 37.773972,
                            'longitude': -122.431297,
                            'radius': 50,
                        }
                    ),
                    locality(
                        {
                            'sourceipaddress': '9.8.7.6',
                            'city': 'Toronto',
                            'country': 'CA',
                            'lastaction': toUTC(datetime.now()) - timedelta(minutes=5),
                            'latitude': 43.6529,
                            'longitude': -79.3849,
                            'radius': 50,
                        }
                    ),
                ],
            )
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
    alert_classname = 'AlertGeoModel'

    default_event = {
        '_source': {
            'details': {
                'sourceipaddress': '1.2.3.4',
                'sourceipgeolocation': {
                    'city': 'Sherbrooke',
                    'country_code': 'CA',
                    'latitude': 45.3397,
                    'longitude': -72.013,
                },
                'username': 'tester1',
            },
            'tags': ['auth0'],
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
                    'longitude': -71.8988,
                },
                'username': 'tester1',
            },
            'tags': ['auth0'],
        }
    }

    default_alert = {
        'category': 'geomodel',
        'summary': 'tester1 seen in Sherbrooke,CA then Sherbrooke,CA',
        'details': {'username': 'tester1'},
        'severity': 'INFO',
        'tags': ['geomodel'],
    }

    events = [
        AlertTestSuite.create_event(default_event),
        AlertTestSuite.create_event(same_city_event),
    ]
    test_cases = [
        NegativeAlertTestCase(
            description='Does not fire within the same actual city', events=events
        )
    ]

    @freeze_time('2017-01-01 01:00:00', tz_offset=0)
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


class TestMultipleEventsInWindow(AlertTestSuite):
    alert_filename = 'geomodel_location'
    alert_classname = 'AlertGeoModel'

    default_event = {
        '_source': {
            'details': {
                'sourceipaddress': '5.6.7.8',
                'username': 'tester1',
                'sourceipgeolocation': {
                    'city': 'Toronto',
                    'country_code': 'CA',
                    'latitude': 43.6529,
                    'longitude': -79.3849,
                },
            },
            'tags': ['auth0'],
        }
    }
    outside_distance_event = {
        '_source': {
            'details': {
                'sourceipaddress': '1.2.3.4',
                'username': 'tester1',
                'sourceipgeolocation': {
                    'city': 'San Francisco',
                    'country_code': 'US',
                    'latitude': 37.773972,
                    'longitude': -122.431297,
                },
            },
            'tags': ['auth0'],
        }
    }

    default_alert = {
        'category': 'geomodel',
        'summary': 'tester1 seen in Toronto,CA then San Francisco,US',
        'details': {
            'username': 'tester1',
            'hops': [
                {
                    'origin': {
                        'ip': '5.6.7.8',
                        'city': 'Toronto',
                        'country': 'CA',
                        'latitude': 43.6529,
                        'longitude': -79.3849,
                        'geopoint': '43.6529,-79.3849',
                    },
                    'destination': {
                        'ip': '1.2.3.4',
                        'city': 'San Francisco',
                        'country': 'US',
                        'latitude': 37.773972,
                        'longitude': -122.431297,
                        'geopoint': '37.773972,-122.431297',
                    },
                }
            ],
        },
        'severity': 'INFO',
        'tags': ['geomodel'],
    }

    events = [
        AlertTestSuite.create_event(default_event),
        AlertTestSuite.create_event(outside_distance_event),
    ]
    events[0]['_source'][
        'utctimestamp'
    ] = AlertTestSuite.subtract_from_timestamp_lambda({'minutes': 4})
    events[0]['_source'][
        'receivedtimestamp'
    ] = AlertTestSuite.subtract_from_timestamp_lambda({'minutes': 4})
    events[1]['_source'][
        'utctimestamp'
    ] = AlertTestSuite.subtract_from_timestamp_lambda({'minutes': 1})
    events[1]['_source'][
        'receivedtimestamp'
    ] = AlertTestSuite.subtract_from_timestamp_lambda({'minutes': 1})
    test_cases = [
        PositiveAlertTestCase(
            description='Does fire when search window contains 2 events with different locations',
            events=events,
            expected_alert=default_alert,
        )
    ]

    @freeze_time('2017-01-01 01:00:00', tz_offset=0)
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


class TestExpiredState(AlertTestSuite):
    alert_filename = 'geomodel_location'
    alert_classname = 'AlertGeoModel'

    default_event = {
        '_source': {
            'details': {
                'sourceipaddress': '5.6.7.8',
                'username': 'tester1',
                'sourceipgeolocation': {
                    'city': 'Toronto',
                    'country_code': 'CA',
                    'latitude': 43.6529,
                    'longitude': -79.3849,
                },
            },
            'tags': ['auth0'],
        }
    }

    test_cases = [
        NegativeAlertTestCase(
            description='Does not fire if state is expired', events=[default_event]
        )
    ]

    @freeze_time('2017-01-01 01:00:00', tz_offset=0)
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
            state(
                'tester1',
                [
                    locality(
                        {
                            'sourceipaddress': '1.2.3.4',
                            'city': 'San Francisco',
                            'country': 'US',
                            'lastaction': toUTC(datetime.now()) - timedelta(days=2),
                            'latitude': 37.773972,
                            'longitude': -122.431297,
                            'radius': 50,
                        }
                    )
                ],
            )
        ]

        for state in test_states:
            journal(geomodel.Entry.new(state), index)
        self.refresh(index)

    def teardown(self):
        if self.config_delete_indexes:
            self.es_client.delete_index('localities', True)
        super().teardown()


class TestSameCitiesFarAway(AlertTestSuite):
    alert_filename = 'geomodel_location'
    alert_classname = 'AlertGeoModel'

    # Portland Maine
    default_event = {
        '_source': {
            'details': {
                'sourceipaddress': '5.6.7.8',
                'username': 'tester1',
                'sourceipgeolocation': {
                    'city': 'Portland',
                    'country_code': 'US',
                    'latitude': 43.6614,
                    'longitude': -70.2553,
                },
            },
            'tags': ['auth0'],
        }
    }

    # Portland, Oregon
    oregon_event = {
        '_source': {
            'details': {
                'sourceipaddress': '1.2.3.4',
                'username': 'tester1',
                'sourceipgeolocation': {
                    'city': 'Portland',
                    'country_code': 'US',
                    'latitude': 45.5234,
                    'longitude': -122.6762,
                },
            },
            'tags': ['auth0'],
        }
    }

    default_alert = {
        'category': 'geomodel',
        'summary': 'tester1 seen in Portland,US then Portland,US',
        'details': {
            'username': 'tester1',
            'hops': [
                {
                    'origin': {
                        'ip': '5.6.7.8',
                        'city': 'Portland',
                        'country': 'US',
                        'latitude': 43.6614,
                        'longitude': -70.2553,
                        'geopoint': '43.6614,-70.2553',
                    },
                    'destination': {
                        'ip': '1.2.3.4',
                        'city': 'Portland',
                        'country': 'US',
                        'latitude': 45.5234,
                        'longitude': -122.6762,
                        'geopoint': '45.5234,-122.6762',
                    },
                }
            ],
        },
        'severity': 'INFO',
        'tags': ['geomodel'],
    }

    events = [
        AlertTestSuite.create_event(default_event),
        AlertTestSuite.create_event(oregon_event),
    ]
    events[0]['_source'][
        'utctimestamp'
    ] = AlertTestSuite.subtract_from_timestamp_lambda({'minutes': 3})
    events[0]['_source'][
        'receivedtimestamp'
    ] = AlertTestSuite.subtract_from_timestamp_lambda({'minutes': 3})

    test_cases = [
        PositiveAlertTestCase(
            description='Does fire if events from same cities but not geographic location',
            events=events,
            expected_alert=default_alert,
        )
    ]

    @freeze_time('2017-01-01 01:00:00', tz_offset=0)
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


class TestMultipleImpossibleJourneys(AlertTestSuite):
    alert_filename = 'geomodel_location'
    alert_classname = 'AlertGeoModel'

    # Portland, Oregon
    default_event = {
        '_source': {
            'details': {
                'sourceipaddress': '1.2.3.4',
                'username': 'tester1',
                'sourceipgeolocation': {
                    'city': 'Portland',
                    'country_code': 'US',
                    'latitude': 45.5234,
                    'longitude': -122.6762,
                },
            },
            'tags': ['auth0'],
        }
    }

    # Toronto, Ontario
    toronto_event = {
        '_source': {
            'details': {
                'sourceipaddress': '5.4.3.2',
                'username': 'tester1',
                'sourceipgeolocation': {
                    'city': 'Toronto',
                    'country_code': 'CA',
                    'latitude': 43.6529,
                    'longitude': -79.3843,
                },
            },
            'tags': ['auth0'],
        }
    }

    st_petersburg_event = {
        '_source': {
            'details': {
                'sourceipaddress': '12.34.45.56',
                'username': 'tester1',
                'sourceipgeolocation': {
                    'city': 'Saint Petersburg',
                    'country_code': 'RU',
                    'latitude': 59.9343,
                    'longitude': 30.3351,
                },
            },
            'tags': ['auth0'],
        }
    }

    events = [
        AlertTestSuite.create_event(evt)
        for evt in [default_event, toronto_event, st_petersburg_event]
    ]

    default_alert = {
        'category': 'geomodel',
        'summary': _summary_from_events(events),
        'details': {'username': 'tester1', 'hops': _hops_from_events(events)},
        'severity': 'INFO',
        'tags': ['geomodel'],
    }

    # Set Toronto and Saint Petersburg 5 and 10 minutes after Portland.
    events[0]['_source'][
        'utctimestamp'
    ] = AlertTestSuite.subtract_from_timestamp_lambda({'minutes': 5})
    events[0]['_source'][
        'receivedtimestamp'
    ] = AlertTestSuite.subtract_from_timestamp_lambda({'minutes': 5})
    events[1]['_source'][
        'utctimestamp'
    ] = AlertTestSuite.subtract_from_timestamp_lambda({'minutes': 2})
    events[1]['_source'][
        'receivedtimestamp'
    ] = AlertTestSuite.subtract_from_timestamp_lambda({'minutes': 2})

    test_cases = [
        PositiveAlertTestCase(
            description='Alert fires with two hops for three different cities',
            events=events,
            expected_alert=default_alert,
        )
    ]

    @freeze_time('2017-01-01 01:00:00', tz_offset=0)
    def setup(self):
        super().setup()

        index = 'localities'
        if self.config_delete_indexes:
            self.es_client.delete_index(index, True)

        self.es_client.create_index(index)
        self.refresh(index)

    def teardown(self):
        if self.config_delete_indexes:
            self.es_client.delete_index('localities', True)
        super().teardown()


class TestDifferentIPsSameLocation(AlertTestSuite):
    alert_filename = 'geomodel_location'
    alert_classname = 'AlertGeoModel'

    default_event = {
        '_source': {
            'details': {
                'sourceipaddress': '1.2.3.4',
                'username': 'tester1',
                'sourceipgeolocation': {
                    'city': 'Portland',
                    'country_code': 'US',
                    'latitude': 45.5234,
                    'longitude': -122.6762,
                },
            },
            'tags': ['auth0'],
        }
    }

    another_event = {
        '_source': {
            'details': {
                'sourceipaddress': '53.12.88.76',
                'username': 'tester1',
                'sourceipgeolocation': {
                    'city': 'Portland',
                    'country_code': 'US',
                    'latitude': 45.5234,
                    'longitude': -122.6762,
                },
            },
            'tags': ['auth0'],
        }
    }

    test_cases = [
        NegativeAlertTestCase(
            description='Should not fire for event & state in the same location',
            events=[default_event]),
        NegativeAlertTestCase(
            description='Should not fire for events in the same location',
            events=[default_event, another_event]),
    ]

    @freeze_time('2017-01-01 01:00:00', tz_offset=0)
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

        test_state = state('tester1', [
            locality(
                {
                    'sourceipaddress': '53.12.88.76',
                    'city': 'Portland',
                    'country': 'US',
                    'lastaction': toUTC(datetime.now()) - timedelta(minutes=2),
                    'latitude': 45.5234,
                    'longitude': -122.6762,
                    'radius': 50,
                }
            ),
            locality(
                {
                    'sourceipaddress': '1.2.3.4',
                    'city': 'Portland',
                    'country': 'US',
                    'lastaction': toUTC(datetime.now()) - timedelta(minutes=3),
                    'latitude': 45.5234,
                    'longitude': -122.6762,
                    'radius': 50,
                }
            )
        ])

        journal(geomodel.Entry.new(test_state), index)
        self.refresh(index)

    def teardown(self):
        if self.config_delete_indexes:
            self.es_client.delete_index('localities', True)
        super().teardown()


class TestAlreadyProcessedEvents(AlertTestSuite):
    alert_filename = 'geomodel_location'
    alert_classname = 'AlertGeoModel'

    default_event = {
        '_source': {
            'details': {
                'sourceipaddress': '1.2.3.4',
                'username': 'tester1',
                'sourceipgeolocation': {
                    'city': 'Portland',
                    'country_code': 'US',
                    'latitude': 45.5234,
                    'longitude': -122.6762,
                },
            },
            'tags': ['auth0'],
        }
    }

    events = [
        AlertTestSuite.create_event(default_event),
    ]
    events[0]['_source']['utctimestamp'] = AlertTestSuite.subtract_from_timestamp_lambda({'minutes': 4})

    test_cases = [
        NegativeAlertTestCase(
            description='Should not fire if encounters older events than state file',
            events=events
        )
    ]

    @freeze_time('2017-01-01 01:00:00', tz_offset=0)
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

        test_state = state('tester1', [
            locality(
                {
                    'sourceipaddress': '1.2.3.4',
                    'city': 'Portland',
                    'country': 'US',
                    'lastaction': toUTC(datetime.now()),
                    'latitude': 45.5234,
                    'longitude': -122.6762,
                    'radius': 50,
                }
            )
        ])

        journal(geomodel.Entry.new(test_state), index)
        self.refresh(index)

    def teardown(self):
        if self.config_delete_indexes:
            self.es_client.delete_index('localities', True)
        super().teardown()


class TestSearchWindowDynamic(AlertTestSuite):
    alert_filename = 'geomodel_location'
    alert_classname = 'AlertGeoModel'

    default_event = {
        '_source': {
            'details': {
                'sourceipaddress': '5.6.7.8',
                'username': 'tester1',
                'sourceipgeolocation': {
                    'city': 'Toronto',
                    'country_code': 'CA',
                    'latitude': 43.6529,
                    'longitude': -79.3849,
                },
            },
            'tags': ['auth0'],
        }
    }
    outside_distance_event = {
        '_source': {
            'details': {
                'sourceipaddress': '1.2.3.4',
                'username': 'tester1',
                'sourceipgeolocation': {
                    'city': 'San Francisco',
                    'country_code': 'US',
                    'latitude': 37.773972,
                    'longitude': -122.431297,
                },
            },
            'tags': ['auth0'],
        }
    }

    events = [
        AlertTestSuite.create_event(default_event),
        AlertTestSuite.create_event(outside_distance_event),
    ]
    events[0]['_source']['utctimestamp'] = AlertTestSuite.subtract_from_timestamp_lambda({'minutes': 4})
    events[0]['_source']['receivedtimestamp'] = AlertTestSuite.subtract_from_timestamp_lambda({'minutes': 4})
    test_cases = [
        NegativeAlertTestCase(
            description='Does not fire if one event is outside of dynamic search window',
            events=events
        )
    ]

    @freeze_time('2017-01-01 01:00:00', tz_offset=0)
    def setup(self):
        super().setup()

        index = 'localities'
        if self.config_delete_indexes:
            self.es_client.delete_index(index, True)
            self.es_client.create_index(index)

        journal = geomodel.wrap_journal(self.es_client)
        exec_state_store = execution.store(self.es_client)

        def state(username, locs):
            return geomodel.State('locality', username, locs)

        def locality(cfg):
            return geomodel.Locality(**cfg)

        record = execution.Record.new(execution.ExecutionState.new(
            toUTC(datetime.now()) - timedelta(minutes=2)))
        exec_state_store(record, index)
        
        self.refresh(index)

    def teardown(self):
        if self.config_delete_indexes:
            self.es_client.delete_index('localities', True)
        super().teardown()
