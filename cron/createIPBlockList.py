#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
# Copyright (c) 2014 Mozilla Corporation
#
# Contributors:
# Jeff Bryner jbryner@mozilla.com

import boto
import boto.s3
import logging
import netaddr
import sys
from datetime import datetime
from datetime import timedelta
from configlib import getConfig, OptionParser
from logging.handlers import SysLogHandler
from pymongo import MongoClient

import os
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../lib'))
from utilities.toUTC import toUTC


logger = logging.getLogger(sys.argv[0])


def loggerTimeStamp(self, record, datefmt=None):
    return toUTC(datetime.now()).isoformat()


def initLogger():
    logger.level = logging.INFO
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    formatter.formatTime = loggerTimeStamp
    if options.output == 'syslog':
        logger.addHandler(
            SysLogHandler(
                address=(options.sysloghostname, options.syslogport)))
    else:
        sh = logging.StreamHandler(sys.stderr)
        sh.setFormatter(formatter)
        logger.addHandler(sh)


def aggregateIPs(attackers):
    iplist = []

    # We don't want to block ips forever,
    # so only care about the ips the past 3 months
    threshold_days = 30 * 3
    timelimit = datetime.now() - timedelta(days=threshold_days)

    ips = attackers.aggregate([
        {"$sort": {"lastseentimestamp": -1}},
        {"$match": {"category": options.category}},
        {"$match": {"lastseentimestamp": {"$gte": timelimit}}},
        {"$match": {"indicators.ipv4address": {"$exists": True}}},
        {"$group": {"_id": {"ipv4address": "$indicators.ipv4address"}}},
        {"$unwind": "$_id.ipv4address"},
        {"$limit": options.iplimit}
    ])

    if 'result' in ips.keys():
        for i in ips['result']:
            whitelisted = False
            logger.debug('working {0}'.format(i))
            ipcidr=netaddr.IPNetwork(i['_id']['ipv4address'])
            if not ipcidr.ip.is_loopback() and not ipcidr.ip.is_private() and not ipcidr.ip.is_reserved():
                for i in options.ipwhitelist:
                    if ipcidr in i:
                        logger.debug('whitelisted' + str(ipcidr))
                        whitelisted = True

                #strip any host bits 192.168.10/24 -> 192.168.0/24
                ipcidrnet=str(ipcidr.cidr)
                if ipcidrnet not in iplist and not whitelisted:
                    iplist.append(ipcidrnet)
            else:
                logger.debug('invalid:' + ip)
    return iplist


def main():
    logger.debug('starting')
    logger.debug(options)
    try:
        client = MongoClient(options.mongohost, options.mongoport)
        # use meteor db/attackers collection
        mozdefdb = client.meteor
        attackers=mozdefdb['attackers']
        attackers.ensure_index([('lastseentimestamp',-1)])
        attackers.ensure_index([('category',1)])
        IPList = aggregateIPs(attackers)
        with open(options.outputfile, 'w') as outputfile:
            for ip in IPList:
                outputfile.write("{0}\n".format(ip))
        outputfile.close()

    except ValueError as e:
        logger.error("Exception %r generating IP block list" % e)


def initConfig():
    # output our log to stdout or syslog
    options.output = getConfig('output', 'stdout', options.configfile)
    # syslog hostname
    options.sysloghostname = getConfig('sysloghostname',
                                       'localhost',
                                       options.configfile)
    # syslog port
    options.syslogport = getConfig('syslogport', 514, options.configfile)

    # mongo instance
    options.mongohost = getConfig('mongohost', 'localhost', options.configfile)
    options.mongoport = getConfig('mongoport', 3001, options.configfile)

    # CIDR whitelist as a comma separted list of 8.8.8.0/24 style masks
    options.ipwhitelist = list()
    for i in list(getConfig('ipwhitelist', '127.0.0.1/32', options.configfile).split(',')):
        options.ipwhitelist.append(netaddr.IPNetwork(i))

    # Output File Name
    options.outputfile = getConfig('outputfile', 'ipblocklist.txt', options.configfile)

    # Category to choose
    options.category = getConfig('category', 'bruteforcer', options.configfile)

    # Max IPs to emit
    options.iplimit = getConfig('iplimit', 1000, options.configfile)

    # AWS creds
    options.aws_access_key_id=getConfig('aws_access_key_id','',options.configfile)          #aws credentials to use to connect to mozilla_infosec_blocklist
    options.aws_secret_access_key=getConfig('aws_secret_access_key','',options.configfile)

def s3_upload_file(file_path, bucket_name, key_name):
    """
    Upload a file to the given s3 bucket and return a template url.
    """
    conn = boto.connect_s3(aws_access_key_id=options.aws_access_key_id,aws_secret_access_key=options.aws_secret_access_key)
    try:
        bucket = conn.get_bucket(bucket_name, validate=False)
    except boto.exception.S3ResponseError as e:
        conn.create_bucket(bucket_name)
        bucket = conn.get_bucket(bucket_name, validate=False)


    key = boto.s3.key.Key(bucket)
    key.key = key_name
    key.set_contents_from_filename(file_path)

    key.set_acl('public-read')
    url = "https://s3.amazonaws.com/{}/{}".format(bucket.name, key.name)
    print( "URL: {}".format(url))
    return url

if __name__ == '__main__':
    parser = OptionParser()
    parser.add_option(
        "-c",
        dest='configfile',
        default=sys.argv[0].replace('.py', '.conf'),
        help="configuration file to use")
    (options, args) = parser.parse_args()
    initConfig()
    initLogger()
    main()
    s3_upload_file('/opt/mozdef/envs/mozdef/static/ipblocklist.txt', 'mozilla_infosec_blocklist','qaipblocklist')
