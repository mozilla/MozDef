import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), "../../../alerts/lib"))
from alerttask import add_hostname_to_ip

import mock
import socket


def reverse_lookup(ip):
    if ip == '10.1.1.1':
        return ('test.domain.com', ip)
    if ip == '8.8.8.8':
        raise socket.herror


class TestAddHostnameToIP(object):
    def setup(self):
        self.formatted_string = '{0} ({1})'

    def test_internal_hostname(self):
        with mock.patch("socket.gethostbyaddr", side_effect=reverse_lookup):
            hostname_info = add_hostname_to_ip('10.1.1.1', self.formatted_string)
        assert hostname_info == '10.1.1.1 (test.domain.com)'

    def test_external_hostname(self):
        with mock.patch("socket.gethostbyaddr", side_effect=reverse_lookup):
            hostname_info = add_hostname_to_ip('8.8.8.8', self.formatted_string)
        assert hostname_info == '8.8.8.8'
