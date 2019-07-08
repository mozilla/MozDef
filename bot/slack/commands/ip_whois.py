import netaddr
from ipwhois import IPWhois

from mozdef_util.utilities.is_ip import is_ip


class Command():
    def __init__(self):
        self.command_name = '!ipwhois'
        self.help_text = 'Perform a whois lookup on an ip address'

    def handle_command(self, parameters):
        response = ""
        for ip_token in parameters:
            if is_ip(ip_token):
                ip = netaddr.IPNetwork(ip_token)[0]
                if (not ip.is_loopback() and not ip.is_private() and not ip.is_reserved()):
                    whois = IPWhois(ip).lookup_whois()
                    description = whois['nets'][0]['description']
                    response += "{0} description: {1}\n".format(ip_token, description)
                else:
                    response += "{0}: hrm...loopback? private ip?\n".format(ip_token)
            else:
                response = "{0} is not an IP address".format(ip_token)
        return response
