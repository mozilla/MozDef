import pygeoip

import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), "../../lib"))
from geo_ip import GeoIP

import pytest
import netaddr


class TestGeoIPInit(object):
    def test_basic_init(self):
        geo_ip = GeoIP()
        assert type(geo_ip.db) is pygeoip.GeoIP


class TestGeoIPLookup(object):
    def setup(self):
        self.geo_ip = GeoIP()

    def test_external_lookup(self):
        geo_dict = self.geo_ip.lookup_ip('8.8.8.8')
        assert geo_dict['country_name'] == 'United States'

    def test_internal_lookup(self):
        geo_dict = self.geo_ip.lookup_ip('10.1.1.1')
        assert geo_dict is None

    def test_incorrect_ip_lookup(self):
        with pytest.raises(netaddr.AddrFormatError):
            self.geo_ip.lookup_ip('blahblahblah')
