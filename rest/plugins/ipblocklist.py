# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# Copyright (c) 2014 Mozilla Corporation

import netaddr
import os
import random
import requests
from configlib import getConfig, OptionParser
from datetime import datetime, timedelta
from pymongo import MongoClient
from mozdef_util.utilities.logger import logger


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


def genMeteorID():
    return('%024x' % random.randrange(16**24))


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
        self.name = "IPBlockList"
        self.description = "IP Block LIst"

        # set my own conf file
        # relative path to the rest index.py file
        self.configfile = './plugins/ipblocklist.conf'
        self.options = None
        if os.path.exists(self.configfile):
            logger.debug('found conf file {0}\n'.format(self.configfile))
        self.initConfiguration()

    def parse_network_whitelist(self, network_whitelist_location):
        networks = []
        with open(network_whitelist_location, "r") as text_file:
            for line in text_file:
                line = line.strip().strip("'").strip('"')
                if isIPv4(line) or isIPv6(line):
                    networks.append(line)
        return networks

    def initConfiguration(self):
        myparser = OptionParser()
        # setup self.options by sending empty list [] to parse_args
        (self.options, args) = myparser.parse_args([])

        # fill self.options with plugin-specific options
        self.options.mongohost = getConfig(
            'mongohost',
            'localhost',
            self.configfile)
        self.options.mongoport = getConfig(
            'mongoport',
            3001,
            self.configfile)

        # CIDR whitelist filename formatted comma separted list of 8.8.8.0/24 style masks
        self.options.network_whitelist_file = getConfig('network_whitelist_file', '/dev/null', self.configfile)

        # CIDR whitelist as comma separated list
        whitelist_networks = getConfig('whitelist_networks', '', self.configfile)
        self.options.whitelist_networks = whitelist_networks.split(',')

        # optional statuspage.io integration
        self.options.statuspage_api_key = getConfig(
            'statuspage_api_key',
            '',
            self.configfile)
        self.options.statuspage_page_id = getConfig(
            'statuspage_page_id',
            '',
            self.configfile)
        self.options.statuspage_url = 'https://api.statuspage.io/v1/pages/{0}/incidents.json'.format(
            self.options.statuspage_page_id)
        self.options.statuspage_component_id = getConfig(
            'statuspage_component_id',
            '',
            self.configfile)
        self.options.statuspage_sub_component_id = getConfig(
            'statuspage_sub_component_id',
            '',
            self.configfile)

    def blockIP(self,
                ipaddress=None,
                comment=None,
                duration=None,
                referenceID=None,
                userID=None
                ):
        try:
            # DB connection/table
            mongoclient = MongoClient(self.options.mongohost, self.options.mongoport)
            ipblocklist = mongoclient.meteor['ipblocklist']

            # good data?
            if (isIPv6(ipaddress) or isIPv4(ipaddress)) and (ipaddress not in netaddr.IPSet(['0.0.0.0'])):
                ipcidr = netaddr.IPNetwork(ipaddress)

                # already in the table?
                ipblock = ipblocklist.find_one({'address': str(ipcidr)})
                # Compute end dates
                end_date = datetime.utcnow() + timedelta(hours=1)
                if duration == '12hr':
                    end_date = datetime.utcnow() + timedelta(hours=12)
                elif duration == '1d':
                    end_date = datetime.utcnow() + timedelta(days=1)
                elif duration == '2d':
                    end_date = datetime.utcnow() + timedelta(days=2)
                elif duration == '3d':
                    end_date = datetime.utcnow() + timedelta(days=3)
                elif duration == '1w':
                    end_date = datetime.utcnow() + timedelta(days=7)
                elif duration == '30d':
                    end_date = datetime.utcnow() + timedelta(days=30)

                if ipblock is None:
                    # insert
                    ipblock = dict()
                    ipblock['_id'] = genMeteorID()
                    # str to get the ip/cidr rather than netblock cidr.
                    # i.e. '1.2.3.4/24' not '1.2.3.0/24'
                    ipblock['address'] = str(ipcidr)
                    ipblock['dateAdded'] = datetime.utcnow()
                    ipblock['dateExpiring'] = end_date
                    ipblock['comment'] = comment
                    ipblock['creator'] = userID
                    ipblock['reference'] = referenceID
                    ref = ipblocklist.insert(ipblock)
                    logger.debug('{0} written to db\n'.format(ref))
                    logger.debug('%s: added to the ipblocklist table\n' % (ipaddress))

                    # send to statuspage.io?
                    if len(self.options.statuspage_api_key) > 1:
                        try:
                            headers = {'Authorization': 'Oauth {0}'.format(self.options.statuspage_api_key)}
                            # send the data as a form post per:
                            # https://doers.statuspage.io/api/v1/incidents/#create-realtime
                            post_data = {
                                'incident[name]': 'block IP {}'.format(str(ipcidr)),
                                'incident[status]': 'resolved',
                                'incident[impact_override]': 'none',
                                'incident[body]': '{} initiated a block of IP {} until {}'.format(
                                    userID,
                                    str(ipcidr),
                                    end_date.isoformat()),
                                'incident[component_ids][]': self.options.statuspage_sub_component_id,
                                'incident[components][{0}]'.format(self.options.statuspage_component_id): "operational"
                            }
                            response = requests.post(self.options.statuspage_url,
                                                     headers=headers,
                                                     data=post_data)
                            if response.ok:
                                logger.debug('%s: notification sent to statuspage.io\n' % (str(ipcidr)))
                            else:
                                logger.error('%s: statuspage.io notification failed %s\n' % (str(ipcidr), response.json()))
                        except Exception as e:
                            logger.error('Error while notifying statuspage.io for %s: %s\n' % (str(ipcidr), e))
                else:
                    logger.debug('%s: is already present in the ipblocklist table...updating\n' % (str(ipcidr)))
                    # Update the document's expiration time and comments
                    ipblock['dateExpiring'] = end_date
                    ipblock['comment'] = comment
                    ipblocklist.replace_one({'_id': ipblock['_id']}, ipblock)
            else:
                logger.error('%s: is not a valid ip address\n' % (ipaddress))
        except Exception as e:
            logger.exception('Error while blocking %s: %s\n' % (ipaddress, e))

    def onMessage(self, request, response):
        '''
        request: http://bottlepy.org/docs/dev/api.html#the-request-object
        response: http://bottlepy.org/docs/dev/api.html#the-response-object

        '''
        response.headers['X-PLUGIN'] = self.description

        # Refresh the ip network list each time we get a message
        self.options.ipwhitelist = self.parse_network_whitelist(self.options.network_whitelist_file)
        for whitelist_value in self.options.whitelist_networks:
            self.options.ipwhitelist.append(whitelist_value)

        ipaddress = None
        comment = None
        duration = None
        referenceID = None
        userid = None
        blockip = False

        try:
            # loop through the fields of the form
            # and fill in our values
            for field in request.json:
                # were we checked?
                if self.name in field:
                    blockip = field[self.name]
                if 'ipaddress' in field:
                    ipaddress = field['ipaddress']
                if 'duration' in field:
                    duration = field['duration']
                if 'comment' in field:
                    comment = field['comment']
                if 'referenceid' in field:
                    referenceID = field['referenceid']
                if 'userid' in field:
                    userid = field['userid']

            if blockip and ipaddress is not None:
                # figure out the CIDR mask
                if isIPv4(ipaddress) or isIPv6(ipaddress):
                    ipcidr = netaddr.IPNetwork(ipaddress)
                    if not ipcidr.ip.is_loopback() \
                       and not ipcidr.ip.is_private() \
                       and not ipcidr.ip.is_reserved():

                        whitelisted = False
                        for whitelist_range in self.options.ipwhitelist:
                            whitelist_network = netaddr.IPNetwork(whitelist_range)
                            if ipcidr in whitelist_network:
                                whitelisted = True
                                logger.debug('{0} is whitelisted as part of {1}\n'.format(ipcidr, whitelist_network))

                        if not whitelisted:
                            self.blockIP(str(ipcidr),
                                         comment,
                                         duration,
                                         referenceID,
                                         userid)
                            logger.info('added {0} to blocklist\n'.format(ipaddress))
                        else:
                            logger.info('not adding {0} to blocklist, it was found in whitelist\n'.format(ipaddress))
        except Exception as e:
            logger.error('Error handling request.json %r \n' % (e))

        return (request, response)
