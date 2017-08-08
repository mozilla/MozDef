import netaddr
import pygeoip
import os


class GeoIP(object):
    def __init__(self):
        geoip_location = os.path.join(os.path.dirname(os.path.abspath(__file__)), "GeoLiteCity.dat")
        self.db = pygeoip.GeoIP(geoip_location, pygeoip.MEMORY_CACHE)

    def lookup_ip(self, ip):
        return self.db.record_by_addr(str(netaddr.IPNetwork(ip)[0]))
