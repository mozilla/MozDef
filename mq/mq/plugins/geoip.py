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


def ipLocation(ip):
    location = ""
    try:
        gi = pygeoip.GeoIP('/home/mozdef/envs/mozdef/bot/GeoLiteCity.dat', pygeoip.MEMORY_CACHE)
        geoDict = gi.record_by_addr(str(netaddr.IPNetwork(ip)[0]))
        if geoDict is not None:
            location = geoDict['country_name']
            if geoDict['country_code'] in ('US'):
                if geoDict['metro_code']:
                    location = location + '/{0}'.format(geoDict['metro_code'])
    except ValueError as e:
        location = ""
    return location


class message(object):
    def __init__(self):
        '''register our criteria for being passed a message
           return a dict with fieldname:None to be sent anything with that field
           return a dict with fieldname:Value to be sent anything with that field/value
           return a string to be sent anything with any field matching that string evaluated as a regex.
           set the priority if you have a preference for order of plugins to run.
           0 goes first, 100 is assumed/default if not sent
        '''
        
        rdict = dict()
        rdict['details'] = dict()
        rdict['details']['sourceipaddress'] = None
        rdict['details']['destinationipaddress'] = None
        self.registration = rdict
        self.priority = 1
    
    def onMessage(self, message):
        if 'details' in message.keys():
            if 'sourceipaddress' in message['details'].keys():
                ipText = message['details']['sourceipaddress']
                if isIP(ipText):
                    ip = netaddr.IPNetwork(ipText)[0]
                    if (not ip.is_loopback() and not ip.is_private() and not ip.is_reserved()):
                        '''lookup geoip info'''
                        message['details']['sourceiplocation'] = ipLocation(ipText)
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
                        message['details']['destinationiplocation'] = ipLocation(ipText)
                else:
                    # invalid ip sent in the field
                    # if we send on, elastic search will error, so set it
                    # to a valid, yet meaningless value
                    message['details']['destinationipaddress'] = '0.0.0.0'
        return message
        
        