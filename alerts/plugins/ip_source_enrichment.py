# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# Copyright (c) 2014 Mozilla Corporation

import json
from operator import add
import os
import re

import functools
import netaddr


CONFIG_FILE = os.path.join(
    os.path.dirname(__file__),
    'ip_source_enrichment.json')


def _find_ip_addresses(string):
    '''List all of the IPv4 and IPv6 addresses found in a string.'''

    ipv4_rx = r'(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)'
    ipv6_rx = r'(([0-9a-fA-F]{1,4}:){7,7}[0-9a-fA-F]{1,4}|([0-9a-fA-F]{1,4}:){1,7}:|([0-9a-fA-F]{1,4}:){1,6}:[0-9a-fA-F]{1,4}|([0-9a-fA-F]{1,4}:){1,5}(:[0-9a-fA-F]{1,4}){1,2}|([0-9a-fA-F]{1,4}:){1,4}(:[0-9a-fA-F]{1,4}){1,3}|([0-9a-fA-F]{1,4}:){1,3}(:[0-9a-fA-F]{1,4}){1,4}|([0-9a-fA-F]{1,4}:){1,2}(:[0-9a-fA-F]{1,4}){1,5}|[0-9a-fA-F]{1,4}:((:[0-9a-fA-F]{1,4}){1,6})|:((:[0-9a-fA-F]{1,4}){1,7}|:)|fe80:(:[0-9a-fA-F]{0,4}){0,4}%[0-9a-zA-Z]{1,}|::(ffff(:0{1,4}){0,1}:){0,1}((25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}(25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])|([0-9a-fA-F]{1,4}:){1,4}:((25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}(25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9]))'

    ipv4 = re.findall(ipv4_rx, string)
    ipv6_map = map(
        lambda match: match[0] if isinstance(match, tuple) else match,
        re.findall(ipv6_rx, string))

    ipv6 = [x for x in ipv6_map]
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
            return functools.reduce(add, found, [])

        if isinstance(value, dict):
            found = [find_ips(item) for item in value.values()]
            return functools.reduce(add, found, [])

        return []

    def ip_in_range(ip):
        return lambda known: netaddr.IPAddress(ip) in netaddr.IPSet([known['range']])

    ips = find_ips(alert)

    alert = alert.copy()

    if 'details' not in alert:
        alert['details'] = {}
    alert['details']['sites'] = []

    for ip in set(ips):
        matching_descriptions = filter(ip_in_range(ip), known_ips)

        for desc in matching_descriptions:
            enriched = desc['format'].format(ip, desc['site'])

            alert['summary'] += '; ' + enriched

            alert['details']['sites'].append({
                'ip': ip,
                'site': desc['site'],
            })

    return alert


def _load_config(file_path):
    '''Private

    Read and parse a file from disk as JSON into a dictionary.
    '''

    with open(file_path) as config_file:
        return json.load(config_file)


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
          "range": "1.2.3.4/8",
          "site": "office1",
          "format": "IPv4 {0} is from {1}"
        },
        {
          "range": "1a2b:3c4d:123::/48",
          "site": "office2",
          "format": "IPv6 {0} is from {1}"
        }
      ]
    }
    ```

    The format string can accept zero to two parameters.  The first
    will be the IP address found and the second will be the
    value of the corresponding 'site'.

    The modified alert will have a `details.sites` field added to it,
    with the following form:

    ```json
    {
      "details": {
        "sites": [
          {
            "ip": "1.2.3.4",
            "site": "office1"
          },
          {
            "ip": "1a2b:3c4d:123::",
            "site": "office2"
          }
        ]
      }
    }
    ```
    '''

    def __init__(self):
        # Run plugin on all alerts
        self.registration = ['*']
        self._config = _load_config(CONFIG_FILE)

    def onMessage(self, message):
        known_ips = self._config.get('known', [])

        return enrich(message, known_ips)
