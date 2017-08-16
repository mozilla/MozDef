import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), "../../lib"))
from geo_ip import GeoIP


class TestGeoIPLookup(object):
    def setup(self):
        self.geo_ip = GeoIP()

    # Unfortunately since the db file is not present by default
    # we verify the error
    def test_without_db_file(self):
        geo_dict = self.geo_ip.lookup_ip('129.21.1.40')
        assert geo_dict['error'] == 'No Geolite DB Found!'
