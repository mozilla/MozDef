# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
# Copyright (c) 2014 Mozilla Corporation

import netaddr


CONFIG_FILE = './ip_source_enrichment.json.conf'


def _isIPv4(ip):
    try:
        return netaddr.valid_ipv4(ip)
    except:
        return False


def _isIPv6(ip):
    try:
        return netaddr.valid_ipv6(ip)
    except:
        return False


def _find_ip_addresses(string):
    '''List all of the IPv4 and IPv6 addresses found in a string.'''

    return []


def enrich(self, alert, known_ips):
    '''Add information to alerts containing IP addresses that describes
    the source location of the IP address if it can be determined based
    on a configured mapping.
    '''
    
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
        return enrich(message, self._configj)
