from mozdef_util.geo_ip import GeoIP


class TestGeoIPLookup(object):
    # Unfortunately since the db file is not present by default
    # we verify the error
    def test_without_db_file(self):
        geo_ip = GeoIP("nonexistent_db")
        geo_dict = geo_ip.lookup_ip('129.21.1.40')
        assert geo_dict['error'] == 'No Geolite DB Found!'
