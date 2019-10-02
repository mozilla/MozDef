from datetime import datetime, timedelta
from typing import Optional

from mozdef_util.utilities.toUTC import toUTC
from mozdef_util.query_models import SearchQuery

import alerts.geomodel.config as config
import alerts.geomodel.locality as locality

from tests.unit_test_suite import UnitTestSuite


def query_interface(results: locality.Entry) -> locality.QueryInterface:
    '''Produce a `QueryInterface` that just returns the provided results.
    '''

    def closure(q: SearchQuery, esi: str) -> Optional[locality.Entry]:
        return results

    return closure


class TestLocalityElasticSearch(UnitTestSuite):
    '''Tests for the `locality` module that interact with ES.
    '''

    def test_simple_query(self):
        objs = [
            {
                'type_': 'locality',
                'username': 'tester1',
                'localities': [
                    {
                        'sourceipaddress': '1.2.3.4',
                        'city': 'Toronto',
                        'country': 'CA',
                        'lastaction': toUTC(datetime.now()),
                        'latitude': 43.6529,
                        'longitude': -79.3849,
                        'radius': 50
                    }
                ]
            }
        ]

        for obj in objs:
            self.populate_test_event(obj)

        self.refresh(self.event_index_name)

        query_iface = locality.wrap_query(self.es_client)
        loc_cfg = config.Localities(self.event_index_name, 30, 50.0)

        entry = locality.find(query_iface, 'tester1', loc_cfg.es_index)

        assert entry is not None
        assert entry.state.username == 'tester1'

    def test_journaling(self):
        journal = locality.wrap_journal(self.es_client)

        test_entry = locality.Entry(
            'testingid1', locality.State('locality', 't1', [
                locality.Locality(
                    sourceipaddress='1.2.3.4',
                    city='Toronto',
                    country='CA',
                    lastaction=toUTC(datetime.now()) - timedelta(days=3),
                    latitude=43.6529,
                    longitude=-79.3849,
                    radius=50),
                locality.Locality(
                    sourceipaddress='32.64.128.255',
                    city='Berlin',
                    country='DE',
                    lastaction=toUTC(datetime.now()) - timedelta(minutes=30),
                    latitude=52.520008,
                    longitude=13.404954,
                    radius=50)
            ]))

        journal(test_entry, self.event_index_name)

        self.refresh(self.event_index_name)

        query_iface = locality.wrap_query(self.es_client)
        loc_cfg = config.Localities(self.event_index_name, 30, 50.0)

        entry = locality.find(query_iface, 't1', loc_cfg.es_index)

        assert entry is not None
        assert entry.state.username == 't1'


class TestLocality:
    '''unit tests for the `locality` module.
    '''

    def test_update_localities(self):
        from_es = locality.State('locality', 'user1', [
            locality.Locality(
                sourceipaddress='1.2.3.4',
                city='Toronto',
                country='CA',
                lastaction=toUTC(datetime.now()) - timedelta(days=3),
                latitude=43.6529,
                longitude=-79.3849,
                radius=50)
        ])

        from_events = locality.State('locality', 'user1', [
            locality.Locality(
                sourceipaddress='1.2.3.4',
                city='Toronto',
                country='CA',
                lastaction=toUTC(datetime.now()) - timedelta(minutes=30),
                latitude=43.6529,
                longitude=-79.3849,
                radius=50)
        ])

        update = locality.update(from_es, from_events)

        last_action = update.state.localities[0].lastaction
        hour_ago = toUTC(datetime.now()) - timedelta(hours=1)

        assert update.did_update
        assert update.state.username == 'user1'
        assert last_action > hour_ago

    def test_update_records_new_localities(self):
        from_es = locality.State('locality', 'user1', [
            locality.Locality(
                sourceipaddress='1.2.3.4',
                city='Toronto',
                country='CA',
                lastaction=toUTC(datetime.now()) - timedelta(days=3),
                latitude=43.6529,
                longitude=-79.3849,
                radius=50)
        ])

        from_events = locality.State('locality', 'user1', [
            locality.Locality(
                sourceipaddress='32.64.128.255',
                city='Berlin',
                country='DE',
                lastaction=toUTC(datetime.now()) - timedelta(minutes=30),
                latitude=52.520008,
                longitude=13.404954,
                radius=50)
        ])

        update = locality.update(from_es, from_events)
        cities = [loc.city for loc in update.state.localities]

        assert update.did_update
        assert sorted(cities) == ['Berlin', 'Toronto']

    def test_remove_outdated_removes_old_localities(self):
        test_state = locality.State('locality', 'tester1', [
            locality.Locality(
                sourceipaddress='32.64.128.255',
                city='Berlin',
                country='DE',
                lastaction=toUTC(datetime.now()) - timedelta(days=10),
                latitude=52.520008,
                longitude=13.404954,
                radius=50),
            locality.Locality(
                sourceipaddress='1.2.3.4',
                city='Toronto',
                country='CA',
                lastaction=toUTC(datetime.now()) - timedelta(days=3),
                latitude=43.6529,
                longitude=-79.3849,
                radius=50)
        ])

        update = locality.remove_outdated(test_state, 5)

        assert update.did_update
        assert len(test_state.localities) == 2
        assert len(update.state.localities) == 1
        assert update.state.localities[0].city == 'Toronto'

    def test_from_event_with_missing_data(self):
        bad_events = [
            {
                '__source': 'invalid'
            },
            {
                '_source': {
                    'nottheipaddress': 'somethingelse'
                }
            },
            {
                '_source': {
                    'details': {
                        'sourceipaddress': '1.2.3.4',
                        'notthegeolocation': 'uhoh'
                    }
                }
            }
        ]

        localities = [locality.from_event(evt) for evt in bad_events]

        assert all([loc is None for loc in localities])

    def test_from_event_provides_default_timestamp(self):
        # Missing `utctimestamp`.
        test_event = {
            '_source': {
                'details': {
                    'sourceipaddress': '1.2.3.4',
                    'sourceipgeolocation': {
                        'city': 'Toronto',
                        'country_code': 'CA',
                        'latitude': 43.6529,
                        'longitude': -79.3849
                    }
                }
            }
        }

        loc = locality.from_event(test_event)

        assert loc.lastaction < toUTC(datetime.now())

    def test_from_event_parses_valid_timestamp(self):
        test_event = {
            '_source': {
                'utctimestamp': '2019-07-31T17:56:38.908000+00:00',
                'details': {
                    'sourceipaddress': '1.2.3.4',
                    'sourceipgeolocation': {
                        'city': 'Toronto',
                        'country_code': 'CA',
                        'latitude': 43.6529,
                        'longitude': -79.3849
                    }
                }
            }
        }

        loc = locality.from_event(test_event)

        assert loc.sourceipaddress == '1.2.3.4'
        assert loc.lastaction.day == 31
