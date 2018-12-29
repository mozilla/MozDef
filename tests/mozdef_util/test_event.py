from mozdef_util.event import Event
from mozdef_util.utilities.toUTC import toUTC
import socket


class MockHostname(object):
    def hostname(self):
        return 'randomhostname'


class TestEvent(object):

    def setup(self):
        self.params = {
            'summary': 'example summary',
            'somefield': 'HIGH',
        }
        self.event = Event(self.params)

    def test_basic_init(self):
        event = Event()
        assert type(event) is Event

    def test_getitem(self):
        assert self.event['summary'] == self.params['summary']
        assert self.event['somefield'] == self.params['somefield']

    def test_setitem(self):
        assert self.event['summary'] == self.params['summary']
        self.event['summary'] = 'other summary value'
        assert self.event['summary'] == 'other summary value'

    def test_add_required_fields_default(self):
        mock_class = MockHostname()
        socket.gethostname = mock_class.hostname
        self.event.add_required_fields()
        assert self.event['receivedtimestamp'] is not None
        assert toUTC(self.event['receivedtimestamp']).isoformat() == self.event['receivedtimestamp']
        assert self.event['utctimestamp'] is not None
        assert toUTC(self.event['utctimestamp']).isoformat() == self.event['utctimestamp']
        assert self.event['timestamp'] is not None
        assert toUTC(self.event['timestamp']).isoformat() == self.event['timestamp']
        assert self.event['mozdefhostname'] == 'randomhostname'
        assert self.event['tags'] == []
        assert self.event['category'] == 'UNKNOWN'
        assert self.event['hostname'] == 'UNKNOWN'
        assert self.event['processid'] == 'UNKNOWN'
        assert self.event['processname'] == 'UNKNOWN'
        assert self.event['severity'] == 'UNKNOWN'
        assert self.event['source'] == 'UNKNOWN'
        assert self.event['summary'] == 'example summary'
        assert self.event['tags'] == []
        assert self.event['details'] == {}

    def test_add_required_fields(self):
        params = {
            'receivedtimestamp': '2017-09-14T20:05:20.779595+00:00',
            'utctimestamp': '2017-09-14T20:05:20.299387+00:00',
            'timestamp': '2017-09-14T20:05:19.116195+00:00',
            'mozdefhostname': 'randomhostname',
            'category': 'Authentication',
            'hostname': 'host.domain.com',
            'processid': 12345,
            'processname': '/bin/testproc',
            'severity': 'HIGH',
            'source': '/var/log/syslog/mozdef.log',
            'summary': 'example summary',
            'tags': ['example'],
            'details': {
                'firstkey': 'firstvalue',
            }
        }
        event = Event(params)
        event.add_required_fields()
        assert event['receivedtimestamp'] == '2017-09-14T20:05:20.779595+00:00'
        assert event['utctimestamp'] == '2017-09-14T20:05:20.299387+00:00'
        assert event['timestamp'] == '2017-09-14T20:05:19.116195+00:00'
        assert event['mozdefhostname'] == 'randomhostname'
        assert event['category'] == 'Authentication'
        assert event['hostname'] == 'host.domain.com'
        assert event['processid'] == 12345
        assert event['processname'] == '/bin/testproc'
        assert event['severity'] == 'HIGH'
        assert event['source'] == '/var/log/syslog/mozdef.log'
        assert event['summary'] == 'example summary'
        assert event['tags'] == ['example']
        assert event['details'] == {'firstkey': 'firstvalue'}
