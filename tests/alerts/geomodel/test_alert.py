from datetime import datetime, timedelta

from mozdef_util.utilities.toUTC import toUTC

from alerts.geomodel.alert import alert
import alerts.geomodel.locality as locality


class TestAlert:
    '''Unit tests for alert generation.
    '''

    def test_do_not_alert_when_travel_possible(self):
        evts = [
            locality.Locality(
                sourceipaddress='1.2.3.123',
                city='Toronto',
                country='CA',
                lastaction=toUTC(datetime.now()) - timedelta(minutes=5),
                latitude=43.6529,
                longitude=-79.3849,
                radius=50),
            locality.Locality(
                sourceipaddress='123.3.2.1',
                city='San Francisco',
                country='US',
                lastaction=toUTC(datetime.now()) - timedelta(hours=10),
                latitude=37.773972,
                longitude=-122.431297,
                radius=50)
        ]

        alert_produced = alert('tester1', evts, [], 'INFO')

        assert alert_produced is None

    def test_do_alert_when_travel_impossible(self):
        evts = [
            locality.Locality(
                sourceipaddress='1.2.3.123',
                city='Toronto',
                country='CA',
                lastaction=toUTC(datetime.now()) - timedelta(minutes=5),
                latitude=43.6529,
                longitude=-79.3849,
                radius=50),
            locality.Locality(
                sourceipaddress='123.3.2.1',
                city='San Francisco',
                country='US',
                lastaction=toUTC(datetime.now()) - timedelta(hours=1),
                latitude=37.773972,
                longitude=-122.431297,
                radius=50)
        ]

        alert_produced = alert('testuser', evts, [], 'INFO')

        assert alert_produced is not None
        assert alert_produced.username == 'testuser'
        assert alert_produced.hops[0].origin.city == 'San Francisco'
        assert alert_produced.hops[0].destination.city == 'Toronto'

    def test_alerts_include_all_impossible_hops(self):
        evts = [
            locality.Locality(
                sourceipaddress='1.2.3.123',
                city='Toronto',
                country='CA',
                lastaction=toUTC(datetime.now()) - timedelta(minutes=5),
                latitude=43.6529,
                longitude=-79.3849,
                radius=50),
            locality.Locality(
                sourceipaddress='52.32.127.3',
                city='Saint Petersburg',
                country='RU',
                lastaction=toUTC(datetime.now()) - timedelta(minutes=15),
                latitude=59.9343,
                longitude=30.3351,
                radius=50),
            locality.Locality(
                sourceipaddress='123.3.2.1',
                city='San Francisco',
                country='US',
                lastaction=toUTC(datetime.now()) - timedelta(hours=1),
                latitude=37.773972,
                longitude=-122.431297,
                radius=50)
        ]

        alert_produced = alert('tester', evts, [], 'INFO')

        assert alert_produced is not None
        assert len(alert_produced.hops) == 2
        assert alert_produced.hops[0].origin.city == 'San Francisco'
        assert alert_produced.hops[0].destination.city == 'Saint Petersburg'
        assert alert_produced.hops[1].origin.city == 'Saint Petersburg'
        assert alert_produced.hops[1].destination.city == 'Toronto'
