# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
# Copyright (c) 2014 Mozilla Corporation

from operator import add
import os
import re

import netaddr


CONFIG_FILE = os.path.join(
    os.path.dirname(__file__),
    'ip_source_enrichment.json.conf')


def _find_ip_addresses(string):
    '''List all of the IPv4 and IPv6 addresses found in a string.'''

    ipv4_rx = '(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)'
    ipv6_rx = '(([0-9a-fA-F]{1,4}:){7,7}[0-9a-fA-F]{1,4}|([0-9a-fA-F]{1,4}:){1,7}:|([0-9a-fA-F]{1,4}:){1,6}:[0-9a-fA-F]{1,4}|([0-9a-fA-F]{1,4}:){1,5}(:[0-9a-fA-F]{1,4}){1,2}|([0-9a-fA-F]{1,4}:){1,4}(:[0-9a-fA-F]{1,4}){1,3}|([0-9a-fA-F]{1,4}:){1,3}(:[0-9a-fA-F]{1,4}){1,4}|([0-9a-fA-F]{1,4}:){1,2}(:[0-9a-fA-F]{1,4}){1,5}|[0-9a-fA-F]{1,4}:((:[0-9a-fA-F]{1,4}){1,6})|:((:[0-9a-fA-F]{1,4}){1,7}|:)|fe80:(:[0-9a-fA-F]{0,4}){0,4}%[0-9a-zA-Z]{1,}|::(ffff(:0{1,4}){0,1}:){0,1}((25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}(25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])|([0-9a-fA-F]{1,4}:){1,4}:((25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}(25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9]))'

    ipv4 = re.findall(ipv4_rx, string)
    ipv6 = map(
        lambda match: match[0] if isinstance(match, tuple) else match,
        re.findall(ipv6_rx, string))

    return ipv4 + ipv6


def enrich(alert, known_ips):
    '''Add information to alerts containing IP addresses that describes
    the source location of the IP address if it can be determined based
    on a configured mapping.
    '''

    def find_ips(value):
        if isinstance(value, str):
            return _find_ip_addresses(value)

        if isinstance(value, list) or isinstance(value, tuple):
            found = [find_ips(item) for item in value]
            return reduce(add, found, [])

        if isinstance(value, dict):
            found = [find_ips(item) for item in value.values()]
            return reduce(add, found, [])

        return []

    ips = find_ips(alert)

    alert = alert.copy()

    for ip in set(ips):
        ip_address = netaddr.IPAddress(ip)

        matching_descriptions = filter(
            lambda known: ip_address in netaddr.IPSet([known['range']]),
            known_ips)

        for desc in matching_descriptions:
            enriched = desc['format'].format(ip)

            alert['summary'] += '; ' + enriched

    return alert


def _load_config(file_path):
    '''Private

    Read and parse a file from disk as JSON into a dictionary.
    '''

    return {}


class message(object):
    '''Alert plugin interface that handles messages (alerts).
    This plugin will look for IP addresses in any of the values of an
    alert dictionary.  For each IP address found, it will append some
    text to the summary of the alert to provide more information
    about where the IP originates from if it is recognized.

    The expected format of the configuration file,
    `ip_source_enrichment.json.conf`, is as follows:

    ```json
    {
      "known": [
        {
          "ipVersion": 4,
          "range": "1.2.3.4/8",
          "format": "IPv4 {1} is known"
        },
        {
          "ipVersion": 6,
          "range": "1a2b:3c4d:123::/48",
          "format": "IPv6 {1} is known"
        }
      ]
    }
    ```
    '''

    def __init__(self):
        self._config = _load_config(CONFIG_FILE)

    def onMessage(self, message):
        known_ips = self._config.get('known', [])

        return enrich(message, known_ips)
