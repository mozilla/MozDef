import netaddr
import os

from mozdef_util.geo_ip import GeoIP
from mozdef_util.utilities.is_ip import is_ip


def ip_location(ip):
    location = ""
    try:
        geoip_data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../../data/GeoLite2-City.mmdb")
        geoip = GeoIP(geoip_data_dir)
        geo_dict = geoip.lookup_ip(ip)
        if geo_dict is not None:
            if 'error' in geo_dict:
                return geo_dict['error']
            location = geo_dict['country_name']
            if geo_dict['country_code'] in ('US'):
                if geo_dict['metro_code']:
                    location = location + '/{0}'.format(geo_dict['metro_code'])
    except Exception:
        location = ""
    return location


class Command():
    def __init__(self):
        self.command_name = '!ipinfo'
        self.help_text = 'Perform a geoip lookup on an ip address'

    def handle_command(self, parameters):
        response = ""
        for ip_token in parameters:
            if is_ip(ip_token):
                ip = netaddr.IPNetwork(ip_token)[0]
                if not (ip.is_loopback() or ip.is_private() or ip.is_reserved()):
                    response += "{0} location: {1}\n".format(ip_token, ip_location(ip_token))
                else:
                    response += "{0}: hrm...loopback? private ip?\n".format(ip_token)
            else:
                response = "{0} is not an IP address".format(ip_token)
        return response
