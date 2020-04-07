# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# Copyright (c) 2014 Mozilla Corporation

import os
import configparser
import netaddr
from boto3.session import Session

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
        self.priority = 50
        self.name = "VPC Blackhole"
        self.description = "VPC blackholing"

        # set my own conf file
        # relative path to the rest index.py file
        self.configfile = './plugins/vpc_blackhole.conf'
        self.options = None
        self.multioptions = []
        if os.path.exists(self.configfile):
            logger.debug('found conf file {0}\n'.format(self.configfile))
            self.initConfiguration()

    def initConfiguration(self):
        myparser = configparser.ConfigParser()
        myparser.read(self.configfile)
        cur_sections = myparser.sections()
        for cur_section in cur_sections:
            if cur_section is not None:
                cur_options = myparser.options(cur_section)
                if cur_options is not None:
                    self.multioptions.append({'region': myparser.get(cur_section, 'region'), 'aws_access_key_id': myparser.get(cur_section, 'aws_access_key_id'), 'aws_secret_access_key': myparser.get(cur_section, 'aws_secret_access_key')})

    def addBlackholeEntry(self,
                          ipaddress=None):
        try:
            if ipaddress is not None and self.multioptions is not None:

                for cur_account in self.multioptions:
                    aws_access_key_id = cur_account['aws_access_key_id']
                    aws_secret_access_key = cur_account['aws_secret_access_key']
                    region_name = cur_account['region']

                    session = Session(aws_access_key_id=aws_access_key_id,
                                      aws_secret_access_key=aws_secret_access_key,
                                      region_name=region_name)

                    ec2 = session.resource('ec2')
                    client = session.client('ec2')

                    response = client.describe_route_tables()
                    for routetable in response['RouteTables']:
                        vpc_id = routetable['VpcId']
                        rt_id = routetable['RouteTableId']
                        if len(routetable['Associations']) > 0:
                            if 'SubnetId' in routetable['Associations'][0]:
                                subnet_id = routetable['Associations'][0]['SubnetId']
                        logger.debug('{0} {1}\n'.format(rt_id, vpc_id))

                        response = client.describe_network_interfaces(
                            Filters=[
                                {
                                    'Name': 'description',
                                    'Values': [
                                        'blackhole',
                                    ]
                                },
                                {
                                    'Name': 'group-name',
                                    'Values': [
                                        'blackhole',
                                    ]
                                },
                                {
                                    'Name': 'vpc-id',
                                    'Values': [
                                        vpc_id,
                                    ]
                                },
                                {
                                    'Name': 'subnet-id',
                                    'Values': [
                                        subnet_id,
                                    ]
                                },
                            ]
                        )

                        logger.debug('{0}\n'.format(response))
                        if len(response['NetworkInterfaces']) > 0:
                            bheni_id = response['NetworkInterfaces'][0]['NetworkInterfaceId']
                            logger.debug('{0} {1} {2}\n'.format(rt_id, vpc_id, bheni_id))

                            # get a handle to a route table associated with a netsec-private subnet
                            route_table = ec2.RouteTable(rt_id)

                            response = route_table.create_route(
                                DestinationCidrBlock=ipaddress,
                                NetworkInterfaceId=bheni_id,
                            )
                        else:
                            logger.debug('Skipping route table {0} in the VPC {1} - blackhole ENI could not be found\n'.format(rt_id, vpc_id))
                            continue

        except Exception as e:
            logger.error('Error while creating a blackhole entry %s: %r\n' % (ipaddress, e))

    def onMessage(self, request, response):
        '''
        request: http://bottlepy.org/docs/dev/api.html#the-request-object
        response: http://bottlepy.org/docs/dev/api.html#the-response-object

        '''
        # format/validate request.json:
        ipaddress = None
        sendToBHVPC = False

        # loop through the fields of the form
        # and fill in our values
        try:
            for field in request.json:
                # were we checked?
                if self.name in field:
                    sendToBHVPC = field[self.name]
                if 'ipaddress' in field:
                    ipaddress = field['ipaddress']
            # are we configured?
            if self.multioptions is None:
                logger.error("Customs server blockip requested but not configured\n")
                sendToBHVPC = False

            if sendToBHVPC and ipaddress is not None:
                # figure out the CIDR mask
                if isIPv4(ipaddress) or isIPv6(ipaddress):
                    ipcidr = netaddr.IPNetwork(ipaddress)
                    if not ipcidr.ip.is_loopback() \
                       and not ipcidr.ip.is_private() \
                       and not ipcidr.ip.is_reserved():
                        ipaddress = str(ipcidr.cidr)
                        self.addBlackholeEntry(ipaddress)
                        logger.info('Blackholed {0}\n'.format(ipaddress))
        except Exception as e:
            logger.error('Error handling request.json %r \n' % (e))

        return (request, response)
