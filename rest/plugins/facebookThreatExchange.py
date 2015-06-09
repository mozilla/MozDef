# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
# Copyright (c) 2014 Mozilla Corporation
#
# Contributors:
# Jeff Bryner jbryner@mozilla.com

import os
import sys
from configlib import getConfig, OptionParser
from datetime import datetime, timedelta
import json
import netaddr
from pytx import init
from pytx import ThreatIndicator


def isIPv4(ip):
    try:
        # netaddr on it's own considers 1 and 0 to be valid_ipv4
        # so a little sanity check prior to netaddr.
        # Use IPNetwork instead of valid_ipv4 to allow CIDR
        if '.' in ip and len(ip.split('.'))==4:
            # some ips are quoted
            netaddr.IPNetwork(ip.strip("'").strip('"'))
            return True
        else:
            return False
    except:
        return False


def isIPv6(ip):
    try:
        return netaddr.valid_ipv6(ip)
    except:
        return False


class message(object):
    def __init__(self):
        '''register our criteria for being passed a message
           as a list of lower case strings to match with an rest endpoint
           (i.e. blockip matches /blockip)
           set the priority if you have a preference for order of plugins
           0 goes first, 100 is assumed/default if not sent

           Plugins will register in Meteor with attributes:
           name: (as below)
           description: (as below)
           priority: (as below)
           file: "plugins.filename" where filename.py is the plugin code.

           Plugin gets sent main rest options as:
           self.restoptions
           self.restoptions['configfile'] will be the .conf file
           used by the restapi's index.py file.

        '''

        self.registration = ['blockip']
        self.priority = 10
        self.name = "ThreatExchange"
        self.description = "Facebook ThreatExchange"

        # set my own conf file
        # relative path to the rest index.py file
        self.configfile = './plugins/facebookThreatExchange.conf'
        self.options = None
        if os.path.exists(self.configfile):
            sys.stdout.write('found conf file {0}\n'.format(self.configfile))
            self.initConfiguration()

            # set up the threat exchange secret
            init(self.options.appid, self.options.appsecret)


    def initConfiguration(self):
        myparser = OptionParser()
        # setup self.options by sending empty list [] to parse_args
        (self.options, args) = myparser.parse_args([])

        # fill self.options with plugin-specific options
        # change this to your default zone for when it's not specified
        self.options.defaultTimeZone = getConfig('defaulttimezone', 'US/Pacific', self.configfile)

        # threat exchange options
        self.options.appid = getConfig('appid',
                                        '',
                                        self.configfile)
        self.options.appsecret=getConfig('appsecret',
                                         '',
                                         self.configfile)


    def sendToThreatExchange(self,
                            ipaddress=None,
                            comment='malicious IP'):
        try:
            if ipaddress is not None and self.options is not None:

                maliciousActor=ThreatIndicator()
                maliciousActor.indicator= ipaddress
                maliciousActor.threat_type="MALICIOUS_IP"
                maliciousActor.type="IP_ADDRESS"
                maliciousActor.share_level="GREEN"
                maliciousActor.status="MALICIOUS"
                maliciousActor.privacy_type="VISIBLE"
                maliciousActor.description= comment
                maliciousActor.save()

                sys.stdout.write('Sent {0} to threat exchange server\n'.format(ipaddress))

        except Exception as e:
            sys.stderr.write('Error while sending to threatexchange %s: %r\n' % (ipaddress, e))


    def onMessage(self, request, response):
        '''
        request: http://bottlepy.org/docs/dev/api.html#the-request-object
        response: http://bottlepy.org/docs/dev/api.html#the-response-object

        '''
        # format/validate request.json:
        ipaddress = None
        CIDR = None
        comment = 'malicious IP'
        duration = None
        referenceID = None
        userid = None
        sendToThreatExchange = False

        # loop through the fields of the form
        # and fill in our values
        try:
            for i in request.json:
                # were we checked?
                if self.name in i.keys():
                    sendToThreatExchange = i.values()[0]
                if 'ipaddress' in i.keys():
                    ipaddress = i.values()[0]
                if 'duration' in i.keys():
                    duration = i.values()[0]
                if 'comment' in i.keys():
                    comment = i.values()[0]
                if 'referenceID' in i.keys():
                    referenceID = i.values()[0]
                if 'userid' in i.keys():
                    userid = i.values()[0]

            # are we configured?
            if self.options is None:
                sys.stderr.write("ThreatExchange requested but not configured\n")
                sendToThreatExchange = False

            if sendToThreatExchange and ipaddress is not None:
                #figure out the CIDR mask
                if isIPv4(ipaddress) or isIPv6(ipaddress):
                    ipcidr=netaddr.IPNetwork(ipaddress)
                    if not ipcidr.ip.is_loopback() \
                       and not ipcidr.ip.is_private() \
                       and not ipcidr.ip.is_reserved():
                        # split the ip vs cidr mask
                        # threat exchange can't accept CIDR addresses
                        # so send the most significant bit
                        ipaddress, CIDR =  str(ipcidr).split('/')
                        self.sendToThreatExchange(ipaddress, comment)
                        sys.stdout.write ('Sent {0} to threat exchange\n'.format(ipaddress))
        except Exception as e:
            sys.stderr.write('Error handling request.json %r \n'% (e))

        return (request, response)
