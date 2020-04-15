from datetime import datetime, timedelta

from mozdef_util.utilities.toUTC import toUTC

from tests.alerts.alert_test_suite import AlertTestSuite
from tests.alerts.negative_alert_test_case import NegativeAlertTestCase
from tests.alerts.positive_alert_test_case import PositiveAlertTestCase

import alerts.geomodel.locality as geomodel
import alerts.geomodel.execution as execution


# Time at which tests are 'frozen' using freezegun.
_NOW = toUTC(datetime(2017, 1, 1, 1, 0, 0, 0))


def state(username, locs):
    return geomodel.State('locality', username, locs)


def locality(cfg):
    return geomodel.Locality(**cfg)


class GeoModelTest(AlertTestSuite):
    '''A specialized base class for GeoModel tests that may want to create a
    `test_states` class attribute specifying states to populate ElasticSearch
    with before running a test.
    '''

    localities_index = 'localities'

    def setup(self):
        super().setup()

        if self.config_delete_indexes:
            self.es_client.delete_index(GeoModelTest.localities_index, True)
            self.es_client.create_index(GeoModelTest.localities_index)

        journal = geomodel.wrap_journal(self.es_client)

        states = self.test_states if hasattr(self, 'test_states') else []

        for state in states:
            journal(geomodel.Entry.new(state), GeoModelTest.localities_index)

        self.refresh(GeoModelTest.localities_index)

    def teardown(self):
        if self.config_delete_indexes:
            self.es_client.delete_index(GeoModelTest.localities_index, True)

        super().teardown()


class TestAlertGeoModel(GeoModelTest):
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
        'summary': 'tester1 seen in San Francisco,US then Toronto,CA '
        '(3645.78 KM in 16.00 minutes)',
        'details': {
            'username': 'tester1',
            'sourceipaddress': '1.2.3.4',
            'sourceipv4address': '1.2.3.4',
            'hops': [
                {
                    'origin': {
                        'ip': '4.3.2.1',
                        'city': 'San Francisco',
                        'country': 'US',
                        'latitude': 37.773972,
                        'longitude': -122.431297,
                        'observed': (_NOW - timedelta(minutes=16)).isoformat(),
                        'geopoint': '37.773972,-122.431297',
                    },
                    'destination': {
                        'ip': '1.2.3.4',
                        'city': 'Toronto',
                        'country': 'CA',
                        'latitude': 43.6529,
                        'longitude': -79.3849,
                        'observed': _NOW.isoformat(),
                        'geopoint': '43.6529,-79.3849',
                    },
                }
            ],
            'factors': [],
        },
        'severity': 'INFO',
        'tags': ['geomodel'],
    }

    test_states = [
        state(
            'tester1',
            [
                locality(
                    {
                        'sourceipaddress': '4.3.2.1',
                        'city': 'San Francisco',
                        'country': 'US',
                        'lastaction': _NOW - timedelta(minutes=16),
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
                        'lastaction': _NOW - timedelta(hours=50),
                        'country': 'CA',
                        'latitude': 43.6529,
                        'longitude': -79.3849,
                        'radius': 50,
                    }
                )
            ],
        ),
    ]

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


class TestEventOrdering(GeoModelTest):
    '''When events come in indicating geolocation movement has occurred, those
    events will contain a `utctimestamp` field that we want to ensure we sort
    on so that localities are both ordered correctly and so that GeoModel alerts
    correctly identify the IP from which a user is acting.
    '''

    alert_filename = 'geomodel_location'
    alert_classname = 'AlertGeoModel'

    default_event = AlertTestSuite.create_event({
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
        },
    })

    default_event['_source']['utctimestamp'] =\
        AlertTestSuite.subtract_from_timestamp_lambda({'minutes': 0})

    change_location_event = AlertTestSuite.create_event({
        '_source': {
            'details': {
                'sourceipaddress': '4.3.2.1',
                'sourceipgeolocation': {
                    'city': 'San Francisco',
                    'country_code': 'US',
                    'latitude': 37.773972,
                    'longitude': -122.431297,
                },
                'username': 'tester1',
            },
            'tags': ['auth0'],
        },
    })

    change_location_event['_source']['utctimestamp'] =\
        AlertTestSuite.subtract_from_timestamp_lambda({'minutes': -1})

    default_alert = {
        'category': 'geomodel',
        'summary': 'tester1 seen in Toronto,CA then San Francisco,US '
        '(3645.78 KM in 1.00 minutes)',
        'details': {
            'username': 'tester1',
            'sourceipaddress': '4.3.2.1',
            'sourceipv4address': '4.3.2.1',
            'hops': [
                {
                    'origin': {
                        'ip': '1.2.3.4',
                        'city': 'Toronto',
                        'country': 'CA',
                        'latitude': 43.6529,
                        'longitude': -79.3849,
                        'observed': _NOW.isoformat(),
                        'geopoint': '43.6529,-79.3849',
                    },
                    'destination': {
                        'ip': '4.3.2.1',
                        'city': 'San Francisco',
                        'country': 'US',
                        'latitude': 37.773972,
                        'longitude': -122.431297,
                        'observed': (_NOW + timedelta(minutes=1)).isoformat(),
                        'geopoint': '37.773972,-122.431297',
                    },
                },
            ],
            'factors': [],
        },
        'severity': 'INFO',
        'tags': ['geomodel'],
    }

    test_cases = [
        PositiveAlertTestCase(
            description='Alert fires with events sorted into the correct order',
            events=[change_location_event, default_event],
            expected_alert=default_alert,
        ),
    ]


class TestUpdateOrdering(GeoModelTest):
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

    test_states = [
        state(
            'tester1',
            [
                locality(
                    {
                        'sourceipaddress': '1.2.3.4',
                        'city': 'San Francisco',
                        'country': 'US',
                        'lastaction': _NOW - timedelta(minutes=3),
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
                        'lastaction': _NOW - timedelta(minutes=5),
                        'latitude': 43.6529,
                        'longitude': -79.3849,
                        'radius': 50,
                    }
                ),
            ],
        )
    ]


class TestOnePreviousLocality(GeoModelTest):
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
        'summary': 'tester1 seen in Toronto,CA then San Francisco,US '
        '(3645.78 KM in 5.00 minutes)',
        'details': {
            'username': 'tester1',
            'sourceipaddress': '1.2.3.4',
            'sourceipv4address': '1.2.3.4',
            'hops': [
                {
                    'origin': {
                        'ip': '9.8.7.6',
                        'city': 'Toronto',
                        'country': 'CA',
                        'latitude': 43.6529,
                        'longitude': -79.3849,
                        'observed': (_NOW - timedelta(minutes=5)).isoformat(),
                        'geopoint': '43.6529,-79.3849',
                    },
                    'destination': {
                        'ip': '1.2.3.4',
                        'city': 'San Francisco',
                        'country': 'US',
                        'latitude': 37.773972,
                        'longitude': -122.431297,
                        'observed': _NOW.isoformat(),
                        'geopoint': '37.773972,-122.431297',
                    },
                }
            ],
            'factors': [],
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

    test_states = [
        state(
            'tester1',
            [
                locality(
                    {
                        'sourceipaddress': '9.8.7.6',
                        'city': 'Toronto',
                        'country': 'CA',
                        'lastaction': _NOW - timedelta(minutes=5),
                        'latitude': 43.6529,
                        'longitude': -79.3849,
                        'radius': 50,
                    }
                )
            ],
        )
    ]


class TestInitialLocalityPositiveAlert(GeoModelTest):
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
        'summary': 'tester1 seen in San Francisco,US then Toronto,CA '
        '(3645.78 KM in 3.00 minutes)',
        'details': {
            'username': 'tester1',
            'sourceipaddress': '5.6.7.8',
            'sourceipv4address': '5.6.7.8',
            'hops': [
                {
                    'origin': {
                        'ip': '1.2.3.4',
                        'city': 'San Francisco',
                        'country': 'US',
                        'latitude': 37.773972,
                        'longitude': -122.431297,
                        'observed': (_NOW - timedelta(minutes=3)).isoformat(),
                        'geopoint': '37.773972,-122.431297',
                    },
                    'destination': {
                        'ip': '5.6.7.8',
                        'city': 'Toronto',
                        'country': 'CA',
                        'latitude': 43.6529,
                        'longitude': -79.3849,
                        'observed': _NOW.isoformat(),
                        'geopoint': '43.6529,-79.3849',
                    },
                }
            ],
            'factors': [],
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

    test_states = [
        state(
            'tester1',
            [
                locality(
                    {
                        'sourceipaddress': '1.2.3.4',
                        'city': 'San Francisco',
                        'country': 'US',
                        'lastaction': _NOW - timedelta(minutes=3),
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
                        'lastaction': _NOW - timedelta(minutes=5),
                        'latitude': 43.6529,
                        'longitude': -79.3849,
                        'radius': 50,
                    }
                ),
            ],
        )
    ]


class TestSameCitiesOutsideRange(GeoModelTest):
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


class TestMultipleEventsInWindow(GeoModelTest):
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
        'summary': 'tester1 seen in Toronto,CA then San Francisco,US '
        '(3645.78 KM in 3.00 minutes)',
        'details': {
            'username': 'tester1',
            'sourceipaddress': '1.2.3.4',
            'sourceipv4address': '1.2.3.4',
            'hops': [
                {
                    'origin': {
                        'ip': '5.6.7.8',
                        'city': 'Toronto',
                        'country': 'CA',
                        'latitude': 43.6529,
                        'longitude': -79.3849,
                        'observed': (_NOW - timedelta(minutes=4)).isoformat(),
                        'geopoint': '43.6529,-79.3849',
                    },
                    'destination': {
                        'ip': '1.2.3.4',
                        'city': 'San Francisco',
                        'country': 'US',
                        'latitude': 37.773972,
                        'longitude': -122.431297,
                        'observed': (_NOW - timedelta(minutes=1)).isoformat(),
                        'geopoint': '37.773972,-122.431297',
                    },
                }
            ],
            'factors': [],
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


class TestExpiredState(GeoModelTest):
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

    test_states = [
        state(
            'tester1',
            [
                locality(
                    {
                        'sourceipaddress': '1.2.3.4',
                        'city': 'San Francisco',
                        'country': 'US',
                        'lastaction': _NOW - timedelta(days=2),
                        'latitude': 37.773972,
                        'longitude': -122.431297,
                        'radius': 50,
                    }
                )
            ],
        )
    ]


class TestSameCitiesFarAway(GeoModelTest):
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
        'summary': 'tester1 seen in Portland,US then Portland,US '
        '(4082.65 KM in 3.00 minutes)',
        'details': {
            'username': 'tester1',
            'sourceipaddress': '1.2.3.4',
            'sourceipv4address': '1.2.3.4',
            'hops': [
                {
                    'origin': {
                        'ip': '5.6.7.8',
                        'city': 'Portland',
                        'country': 'US',
                        'latitude': 43.6614,
                        'longitude': -70.2553,
                        'observed': (_NOW - timedelta(minutes=3)).isoformat(),
                        'geopoint': '43.6614,-70.2553',
                    },
                    'destination': {
                        'ip': '1.2.3.4',
                        'city': 'Portland',
                        'country': 'US',
                        'latitude': 45.5234,
                        'longitude': -122.6762,
                        'observed': _NOW.isoformat(),
                        'geopoint': '45.5234,-122.6762',
                    },
                }
            ],
            'factors': [],
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


class TestMultipleImpossibleJourneys(GeoModelTest):
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

    default_alert = {
        'category': 'geomodel',
        'summary': 'tester1 seen in Portland,US then Toronto,CA '
        '(3393.90 KM in 3.00 minutes); Toronto,CA then Saint '
        'Petersburg,RU (6855.53 KM in 2.00 minutes)',
        'details': {
            'username': 'tester1',
            'sourceipaddress': '12.34.45.56',
            'sourceipv4address': '12.34.45.56',
            'hops': [
                {
                    'origin': {
                        'ip': '1.2.3.4',
                        'city': 'Portland',
                        'country': 'US',
                        'latitude': 45.5234,
                        'longitude': -122.6762,
                        'observed': (_NOW - timedelta(minutes=5)).isoformat(),
                        'geopoint': '45.5234,-122.6762',
                    },
                    'destination': {
                        'ip': '5.4.3.2',
                        'city': 'Toronto',
                        'country': 'CA',
                        'latitude': 43.6529,
                        'longitude': -79.3843,
                        'observed': (_NOW - timedelta(minutes=2)).isoformat(),
                        'geopoint': '43.6529,-79.3843',
                    },
                },
                {
                    'origin': {
                        'ip': '5.4.3.2',
                        'city': 'Toronto',
                        'country': 'CA',
                        'latitude': 43.6529,
                        'longitude': -79.3843,
                        'observed': (_NOW - timedelta(minutes=2)).isoformat(),
                        'geopoint': '43.6529,-79.3843',
                    },
                    'destination': {
                        'ip': '12.34.45.56',
                        'city': 'Saint Petersburg',
                        'country': 'RU',
                        'latitude': 59.9343,
                        'longitude': 30.3351,
                        'observed': _NOW.isoformat(),
                        'geopoint': '59.9343,30.3351',
                    },
                },
            ],
            'factors': [],
        },
        'severity': 'INFO',
        'tags': ['geomodel'],
    }

    test_cases = [
        PositiveAlertTestCase(
            description='Alert fires with two hops for three different cities',
            events=events,
            expected_alert=default_alert,
        )
    ]


class TestDifferentIPsSameLocation(GeoModelTest):
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
            events=[default_event],
        ),
        NegativeAlertTestCase(
            description='Should not fire for events in the same location',
            events=[default_event, another_event],
        ),
    ]

    test_states = [
        state(
            'tester1',
            [
                locality(
                    {
                        'sourceipaddress': '53.12.88.76',
                        'city': 'Portland',
                        'country': 'US',
                        'lastaction': _NOW - timedelta(minutes=2),
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
                        'lastaction': _NOW - timedelta(minutes=3),
                        'latitude': 45.5234,
                        'longitude': -122.6762,
                        'radius': 50,
                    }
                ),
            ],
        )
    ]


class TestAlreadyProcessedEvents(GeoModelTest):
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

    events = [AlertTestSuite.create_event(default_event)]
    events[0]['_source'][
        'utctimestamp'
    ] = AlertTestSuite.subtract_from_timestamp_lambda({'minutes': 4})

    test_cases = [
        NegativeAlertTestCase(
            description='Should not fire if encounters older events than state file',
            events=events,
        )
    ]

    test_states = [
        state(
            'tester1',
            [
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
            ],
        )
    ]


class TestSearchWindowDynamic(GeoModelTest):
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
    events[0]['_source'][
        'utctimestamp'
    ] = AlertTestSuite.subtract_from_timestamp_lambda({'minutes': 4})
    events[0]['_source'][
        'receivedtimestamp'
    ] = AlertTestSuite.subtract_from_timestamp_lambda({'minutes': 4})
    test_cases = [
        NegativeAlertTestCase(
            description='Does not fire if one event is outside of dynamic search window',
            events=events,
        )
    ]

    def setup(self):
        super().setup()

        exec_state_store = execution.store(self.es_client)

        record = execution.Record.new(
            execution.ExecutionState.new(_NOW - timedelta(minutes=2))
        )

        exec_state_store(record, GeoModelTest.localities_index)

        self.refresh(GeoModelTest.localities_index)
