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
import boto.sqs
from boto.sqs.message import RawMessage

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
        self.name = "fxaCustomsServer"
        self.description = "Firefox Accounts SQS Queue"

        # set my own conf file
        # relative path to the rest index.py file
        self.configfile = './plugins/fxaCustomsServer.conf'
        self.options = None
        if os.path.exists(self.configfile):
            sys.stdout.write('found conf file {0}\n'.format(self.configfile))
            self.initConfiguration()
        

    def initConfiguration(self):
        myparser = OptionParser()
        # setup self.options by sending empty list [] to parse_args
        (self.options, args) = myparser.parse_args([])
        
        # fill self.options with plugin-specific options
        # change this to your default zone for when it's not specified
        self.options.defaultTimeZone = getConfig('defaulttimezone', 'US/Pacific', self.configfile)
        
        # boto options
        self.options.region = getConfig('region',
                                        'us-west-2',
                                        self.configfile)
        self.options.aws_access_key_id=getConfig('aws_access_key_id',
                                                         '',
                                                         self.configfile)
        self.options.aws_secret_access_key=getConfig('aws_secret_access_key',
                                                     '',
                                                     self.configfile)
        self.options.aws_queue_name=getConfig('aws_queue_name',
                                              '',
                                              self.configfile)


    def sendToCustomsServer(self,
                            ipaddress=None):
        try:
            if ipaddress is not None and self.options is not None:
                # connect and send a message like:
                # '{"Message": {"ban": {"ip": "192.168.0.2"}}}'
                # encoded like this:
                # {"Message":"{\"ban\":{\"ip\":\"192.168.0.2\"}}"}
                
                conn = boto.sqs.connect_to_region(self.options.region,
                                                  aws_access_key_id=self.options.aws_access_key_id,
                                                  aws_secret_access_key=self.options.aws_secret_access_key)
                queue = conn.get_queue(self.options.aws_queue_name)

                banMessage = dict(Message=json.dumps(dict(ban=dict(ip=ipaddress))))
                m = RawMessage()
                m.set_body(json.dumps(banMessage))
                queue.write(m)
                sys.stdout.write('Sent {0} to customs server\n'.format(ipaddress))
            
        except Exception as e:
            sys.stderr.write('Error while sending to customs server %s: %r\n' % (ipaddress, e))


    def onMessage(self, request, response):
        '''
        request: http://bottlepy.org/docs/dev/api.html#the-request-object
        response: http://bottlepy.org/docs/dev/api.html#the-response-object
        
        '''        
        # format/validate request.json:
        ipaddress = None
        CIDR = None
        comment = None
        duration = None
        referenceID = None
        userid = None
        sendToCustomsServer = False
        
        # loop through the fields of the form
        # and fill in our values
        try: 
            for i in request.json:
                # were we checked?
                if self.name in i.keys():
                    sendToCustomsServer = i.values()[0]
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
                sys.stderr.write("Customs server blockip requested but not configured\n")
                sendToCustomsServer = False

            if sendToCustomsServer and ipaddress is not None:
                #figure out the CIDR mask
                if isIPv4(ipaddress) or isIPv6(ipaddress):
                    ipcidr=netaddr.IPNetwork(ipaddress)
                    if not ipcidr.ip.is_loopback() \
                       and not ipcidr.ip.is_private() \
                       and not ipcidr.ip.is_reserved():
                        #split the ip vs cidr mask
                        ipaddress, CIDR =  str(ipcidr.cidr).split('/')
                        self.sendToCustomsServer(ipaddress)
                        sys.stdout.write ('Sent {0}/{1} to customs server\n'.format(ipaddress, CIDR))
        except Exception as e:
            sys.stderr.write('Error handling request.json %r \n'% (e))
                
        return (request, response)
