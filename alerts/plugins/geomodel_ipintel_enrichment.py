# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# Copyright (c) 2017 Mozilla Corporation

import json
import os
import typing as types


CONFIG_FILE = os.path.join(
    os.path.dirname(__file__),
    'geomodel_ipintel_enrichment.json')

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
        '''Attempt to load a `Config` from a JSON file.
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

    The alert's summary is also appended with notes about IPs belonging to Tor
    nodes and VPNs when they are detected.  For example, a summary may take the
    form

    > user@mozilla.com seen in Dallas,US then Dumbravita,RO
    > (9293.00 KM in 150.87 minutes); Tor nodes detected: 1.2.3.4, 5.6.7.8
    > ; VPNs detected: 10.11.12.13
    '''

    def __init__(self):
        config = Config.load(CONFIG_FILE)

        self.registration = [config.match_tag]

        with open(config.intel_file_path) as intel_file:
            self._intel = json.load(intel_file)

    def onMessage(self, message):
        alert_tags = message.get('tags', [])

        if self.registration[0] in alert_tags:
            return enrich(message, self._intel)

        return message


def enrich(alert, intel):
    '''Enrich a geomodel alert with intel about IPs that are known Tor exit
    nodes or members of a VPN.
    '''

    # The names of classifications present in the intel source that we want to
    # specifically detect and enrich the alert summary with when detected.
    tor_class = 'TorNode'
    vpn_class = 'VPN'

    details = alert.get('details', {})

    hops = details.get('hops', [])

    ips = [
        hop['origin']['ip']
        for hop in hops
    ]

    if len(hops) > 0:
        ips.append(hops[-1]['destination']['ip'])

    relevant_intel = {
        ip: intel[ip]
        for ip in set(ips)
        if ip in intel
    }

    ip_intel = []

    for ip, records in relevant_intel.items():
        ip_intel.extend([
            {'ip': ip, 'classification': _class, 'threatscore': records[_class]}
            for _class in records
        ])

    tor_nodes = [
        entry['ip']
        for entry in ip_intel
        if entry['classification'] == tor_class
    ]

    vpn_nodes = [
        entry['ip']
        for entry in ip_intel
        if entry['classification'] == vpn_class
    ]

    if len(tor_nodes) > 0:
        alert['summary'] += '; Tor nodes detected: {}'.format(
            ', '.join(tor_nodes))

    if len(vpn_nodes) > 0:
        alert['summary'] += '; VPNs detected: {}'.format(
            ', '.join(vpn_nodes))

    details['ipintel'] = ip_intel

    alert['details'] = details

    return alert
