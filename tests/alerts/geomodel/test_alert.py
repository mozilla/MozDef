from datetime import datetime, timedelta

from mozdef_util.utilities.toUTC import toUTC

from alerts.geomodel.alert import alert
import alerts.geomodel.config as config
import alerts.geomodel.locality as locality


class TestAlert:
    '''Unit tests for alert generation.
    '''

    def test_do_not_alert_on_whitelisted_user(self):
        whitelist = config.Whitelist(users=['testuser1'], cidrs=[])
        state = locality.State('locality', 'testuser1', [])

        alert_produced = alert(state, whitelist)

        assert alert_produced is None

    def test_do_not_alert_on_whitelisted_ips(self):
        whitelist = config.Whitelist(users=[], cidrs=['1.2.3.0/8'])
        state = locality.State('locality', 'testuser', [
            locality.Locality(
                sourceipaddress='1.2.3.123',
                city='Toronto',
                country='CA',
                lastaction=toUTC(datetime.now()) - timedelta(minutes=5),
                latitude=43.6529,
                longitude=-79.3849,
                radius=50)
        ])

        alert_produced = alert(state, whitelist)

        assert alert_produced is None

    def test_do_not_alert_when_travel_possible(self):
        whitelist = config.Whitelist(users=[], cidrs=[])
        state = locality.State('locality', 'testuser', [
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
        ])

        alert_produced = alert(state, whitelist)

        assert alert_produced is None

    def test_do_alert_when_travel_impossible(self):
        whitelist = config.Whitelist(users=[], cidrs=[])
        state = locality.State('locality', 'testuser', [
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
        ])

        alert_produced = alert(state, whitelist)

        assert alert_produced is not None
        assert alert_produced.username == 'testuser'
        assert alert_produced.sourceipaddress == '1.2.3.123'
        assert alert_produced.origin.city == 'Toronto'
