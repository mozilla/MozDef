import mock
import socket
import os
import sys


def reverse_lookup(ip):
    if ip == '10.1.1.1':
        return ('test.domain.com', ip)
    if ip == '8.8.8.8':
        raise socket.herror


class AlertTaskTest(object):
    def teardown(self):
        sys.path.remove(self.alerts_path)
        sys.path.remove(self.alerts_lib_path)
        if 'lib' in sys.modules:
            del sys.modules['lib']

    def setup(self):
        self.alerts_path = os.path.join(os.path.dirname(__file__), "../../../alerts")
        self.alerts_lib_path = os.path.join(os.path.dirname(__file__), "../../../alerts/lib")
        sys.path.insert(0, self.alerts_path)
        sys.path.insert(1, self.alerts_lib_path)
        from lib import alerttask
        self.hostname_from_ip = alerttask.hostname_from_ip
        self.add_hostname_to_ip = alerttask.add_hostname_to_ip


class TestHostnameFromIP(AlertTaskTest):
    def test_good_hostname_from_ip(self):
        with mock.patch("socket.gethostbyaddr", side_effect=reverse_lookup):
            hostname = self.hostname_from_ip('10.1.1.1')
        assert hostname == 'test.domain.com'

    def test_bad_hostname_from_ip(self):
        with mock.patch("socket.gethostbyaddr", side_effect=reverse_lookup):
            hostname = self.hostname_from_ip('8.8.8.8')
        assert hostname is None


class TestAddHostnameToIP(AlertTaskTest):
    def setup(self):
        super().setup()
        self.formatted_string = '{0} ({1})'

    def test_internal_hostname(self):
        with mock.patch("socket.gethostbyaddr", side_effect=reverse_lookup):
            hostname_info = self.add_hostname_to_ip('10.1.1.1', self.formatted_string)
        assert hostname_info == '10.1.1.1 (test.domain.com)'

    def test_external_hostname(self):
        with mock.patch("socket.gethostbyaddr", side_effect=reverse_lookup):
            hostname_info = self.add_hostname_to_ip('8.8.8.8', self.formatted_string)
        assert hostname_info == '8.8.8.8'
