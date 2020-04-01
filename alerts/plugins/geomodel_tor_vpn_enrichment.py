# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# Copyright (c) 2017 Mozilla Corporation

import json
import os
import typing as types


CONFIG_FILE = os.path.join(
    os.path.dirname(__file__),
    'geomodel_tor_vpn_enrichment.json')


class InvalidConfigException(Exception):
    '''An exception raised if a configuration file contains missing or
    unexpected data.
    '''

    def __init__(self, msg):
        super().__init__()

        self.message = msg

# TODO: Switch to dataclasses when we move to Python 3.7+

class Config(types.NamedTuple):
    '''Container for the configuration of the plugin.

    `intel_file_path` is a path to an IP reputation JSON file
    providing information about Tor exit nodes and VPNs.

    `match_tag` is the alert tag to match and run the plugin on.
    '''

    intel_file_path: str
    match_tag: str

    def load(file_path: str) -> 'Config':
        '''Attempt to load a `Config` from a file containing JSON of the
        format required by the plugin.  If the file cannot be read or contains
        improperly-formatted or missing data, this function throws either a:

        * `FileNotFoundException`
        * `json.decoder.JSONDecodeError`
        * `InvalidConfigException`
        '''

        with open(file_path) as cfg_file:
            return Config(**json.load(cfg_file))


class message:
    '''Alert plugin that handles messages (alerts) tagged as geomodel alerts
    produced by `geomodel_location.AlertGeoModel`.  This plugin will enrich such
    alerts with information about Tor exit nodes and/or VPNs identified by any
    of the IP addresses present in the `details.hops` of the alert.

    Specifically, the alert's `details` dict will have a new field `ipintel`
    appended containing the contents of an `IPIntel`.
    '''

    def __init__(self):
        config = Config.load(CONFIG_FILE)

        self.registration = config.match_tag

        with open(config.intel_file_path) as intel_file:
            self._intel = json.load(intel_file)


    def onMessage(self, message):
        alert_tags = message.get('tags', [])

        if self.config.match_tag in alert_tags:
            return enrich(message, self._intel)

        return message


def enrich(alert, intel):
    '''Enrich a geomodel alert with intel about IPs that are known Tor exit
    nodes or members of a VPN.
    '''

    details = alert.get('details', {})

    hops = details.get('hops', [])

    ips = [
        hop['origin']['ip']
        for hop in hops
    ]

    if len(hops) > 0:
        ips.append(hops[-1]['destination']['ip'])

    ip_intel = []

    for ip in ips:
        if ip in intel:
            for _class in intel[ip]:
                new_entry = {
                    'ip': ip,
                    'classification': _class,
                    'threatscore': intel[ip][_class],
                }

                if new_entry not in ip_intel:
                    ip_intel.append(new_entry)

    details['ipintel'] = ip_intel

    alert['details'] = details

    return alert
