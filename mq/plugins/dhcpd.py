# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
# Copyright (c) 2017 Mozilla Corporation

import re


class message(object):
    def __init__(self):
        '''
            Plugin used to parse dhcpd formatted messages
        '''
        self.registration = ['dhcpd']
        self.priority = 10
        self.action_map = {
            'DHCPACK': 'ACK',
            'DHCPREQUEST': 'REQUEST'
        }

    def onMessage(self, message, metadata):
        if 'summary' not in message:
            return (message, metadata)

        for match_text, action in self.action_map.iteritems():
            if message['summary'].startswith(match_text):
                if 'details' not in message:
                    message['details'] = {}
                message['details']['action'] = action

        ipv4_regex = re.compile("(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})")
        ipv4_match = ipv4_regex.search(message['summary'])
        if ipv4_match:
            message['details']['sourceipaddress'] = ipv4_match.group(0)

        mac_address_match = re.search(r'([0-9A-F]{2}[:-]){5}([0-9A-F]{2})', message['summary'], re.I)
        if mac_address_match:
            message['details']['source_mac_address'] = mac_address_match.group(0)

        interface_regex = re.compile(" via (\w+)$")
        interface_match = interface_regex.search(message['summary'])
        if interface_match:
            message['details']['interface'] = interface_match.group(1)

        # DHCPACK on 10.1.2.3 to 00:aa:bb:11:22:de via igb1
        # details.action (ack, etc)
        # details.source_ip: 10.1.2.3
        # details.source_mac: 00:aa:bb:11:22:de
        # details.interface: igb1
        return (message, metadata)
