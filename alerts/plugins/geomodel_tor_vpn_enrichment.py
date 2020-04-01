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


class TorExitNode(types.NamedTuple):
    '''Container for informatuon describing a Tor exit node.
    '''

    placeholder: str


class VPNMember(types.NamedTuple):
    '''Container for information describing an IP belonging to a VPN.
    '''

    placeholder: str


# The intel provided is _one of_ the following types.
Classification = types.Union[
    TorExitNode,
    VPNMember
]

class IPIntel(types.NamedTuple):
    '''A container for intel about IP addresses present in a GeoModel alert that
    either are known to be Tor exit nodes or to belong to a VPN.
    '''

    ip: str
    classification: Classification


class message:
    '''Alert plugin that handles messages (alerts) tagged as geomodel alerts
    produced by `geomodel_location.AlertGeoModel`.  This plugin will enrich such
    alerts with information about Tor exit nodes and/or VPNs identified by any
    of the IP addresses present in the `details.hops` of the alert.

    Specifically, the alert's `details` dict will have a new field `ipintel`
    appended containing the contents of an `IPIntel`.
    '''

    def __init__(self):
        self.config = Config.load(CONFIG_FILE)

        self.registration = self.config.match_tag


    def onMessage(self, message):
        alert_tags = message.get('tags', [])

        if self.config.match_tag in alert_tags:
            return enrich(message, self.config.intel_file_path)

        return message


def enrich(alert, intel_file_path):
    '''Enrich a geomodel alert with intel about IPs that are known Tor exit
    nodes or members of a VPN.
    '''

    return alert
