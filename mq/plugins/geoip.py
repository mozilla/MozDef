# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
# Copyright (c) 2014 Mozilla Corporation
#
# Contributors:
# Jeff Bryner jbryner@mozilla.com

import netaddr
import pygeoip


def isIP(ip):
    try:
        netaddr.IPNetwork(ip)
        return True
    except:
        return False


class message(object):
    def __init__(self):
        '''register our criteria for being passed a message
           as a list of lower case strings or values to match with an event's dictionary of keys or values
           set the priority if you have a preference for order of plugins to run.
           0 goes first, 100 is assumed/default if not sent
        '''
        self.registration = ['sourceipaddress', 'destinationipaddress']
        self.priority = 20
        self.geoip = pygeoip.GeoIP('/home/mozdef/envs/mozdef/bot/GeoLiteCity.dat', pygeoip.MEMORY_CACHE)

    def ipLocation(self, ip):
        location = dict()
        try:
            geoDict = self.geoip.record_by_addr(str(netaddr.IPNetwork(ip)[0]))
            if geoDict is not None:
                return geoDict
            else:
                location['location'] = 'unknown'
        except ValueError as e:
            pass
        return location

    def onMessage(self, message, metadata):
        if 'details' in message.keys():
            if 'sourceipaddress' in message['details'].keys():
                ipText = message['details']['sourceipaddress']
                if isIP(ipText):
                    ip = netaddr.IPNetwork(ipText)[0]
                    if (not ip.is_loopback() and not ip.is_private() and not ip.is_reserved()):
                        '''lookup geoip info'''
                        message['details']['sourceipgeolocation'] = self.ipLocation(ipText)
                else:
                    # invalid ip sent in the field
                    # if we send on, elastic search will error, so set it
                    # to a valid, yet meaningless value
                    message['details']['sourceipaddress'] = '0.0.0.0'

            if 'destinationipaddress' in message['details'].keys():
                ipText = message['details']['destinationipaddress']
                if isIP(ipText):
                    ip = netaddr.IPNetwork(ipText)[0]
                    if (not ip.is_loopback() and not ip.is_private() and not ip.is_reserved()):
                        '''lookup geoip info'''
                        message['details']['destinationipgeolocation'] = self.ipLocation(ipText)
                else:
                    # invalid ip sent in the field
                    # if we send on, elastic search will error, so set it
                    # to a valid, yet meaningless value
                    message['details']['destinationipaddress'] = '0.0.0.0'
        return (message, metadata)
