# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# Copyright (c) 2014 Mozilla Corporation

import netaddr
import os

from mozdef_util.geo_ip import GeoIP


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
        geoip_data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../data/GeoLite2-City.mmdb")
        self.geoip = GeoIP(geoip_data_dir)

    def ipLocation(self, ip):
        location = dict()
        try:
            geoDict = self.geoip.lookup_ip(ip)
            if geoDict is not None:
                return geoDict
            else:
                location['location'] = 'unknown'
        except ValueError:
            pass
        return location

    def onMessage(self, message, metadata):
        if 'details' in message:
            keys = ['source', 'destination']
            for key in keys:
                ip_key = '{0}ipaddress'.format(key)
                if ip_key in message['details']:
                    ipText = message['details'][ip_key]
                    if isIP(ipText):
                        ip = netaddr.IPNetwork(ipText)[0]
                        if (not ip.is_loopback() and not ip.is_private() and not ip.is_reserved()):
                            '''lookup geoip info'''
                            geo_key = '{0}ipgeolocation'.format(key)
                            message['details'][geo_key] = self.ipLocation(ipText)
                            # Add a geo_point coordinates if latitude and longitude exist
                            if 'latitude' in message['details'][geo_key] and 'longitude' in message['details'][geo_key]:
                                if message['details'][geo_key]['latitude'] and message['details'][geo_key]['latitude'] != '' and \
                                   message['details'][geo_key]['longitude'] and message['details'][geo_key]['longitude'] != '':
                                    geopoint_key = '{0}ipgeopoint'.format(key)
                                    message['details'][geopoint_key] = '{0},{1}'.format(
                                        message['details'][geo_key]['latitude'],
                                        message['details'][geo_key]['longitude']
                                    )

                    else:
                        # invalid ip sent in the field
                        # if we send on, elastic search will error, so set it
                        # to a valid, yet meaningless value
                        message['details'][ip_key] = '0.0.0.0'
        return (message, metadata)
