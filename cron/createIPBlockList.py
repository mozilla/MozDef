#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# Copyright (c) 2014 Mozilla Corporation

import boto3
import netaddr
import sys
from datetime import datetime
from datetime import timedelta
from configlib import getConfig, OptionParser
from pymongo import MongoClient

from mozdef_util.utilities.logger import logger


def isIPv4(ip):
    try:
        # netaddr on it's own considers 1 and 0 to be valid_ipv4
        # so a little sanity check prior to netaddr.
        # Use IPNetwork instead of valid_ipv4 to allow CIDR
        if '.' in ip and len(ip.split('.')) == 4:
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


def parse_network_whitelist(network_whitelist_location):
    networks = []
    with open(network_whitelist_location, "r") as text_file:
        for line in text_file:
            line = line.strip().strip("'").strip('"')
            if isIPv4(line) or isIPv6(line):
                networks.append(line)
    return networks


def main():
    logger.debug('starting')
    logger.debug(options)
    try:
        # connect to mongo
        client = MongoClient(options.mongohost, options.mongoport)
        mozdefdb = client.meteor
        ipblocklist = mozdefdb['ipblocklist']
        # ensure indexes
        ipblocklist.create_index([('dateExpiring', -1)])
        # delete any that expired
        ipblocklist.delete_many({'dateExpiring': {"$lte": datetime.utcnow() - timedelta(days=options.expireage)}})

        # Export the blocklist
        ipCursor = mozdefdb['ipblocklist'].aggregate([
            {"$sort": {"dateAdded": -1}},
            {"$match": {"address": {"$exists": True}}},
            {"$match": {
                "$or": [
                    {"dateExpiring": {"$gte": datetime.utcnow()}},
                    {"dateExpiring": {"$exists": False}},
                ]},
             },
            {"$project": {"address": 1}},
            {"$limit": options.iplimit}
        ])
        ips = []
        for ip in ipCursor:
            ips.append(ip['address'])
        uniq_ranges = netaddr.cidr_merge(ips)
        # to text
        with open(options.outputfile, 'w') as outputfile:
            for ip in uniq_ranges:
                outputfile.write("{0}\n".format(ip))
        outputfile.close()
        # to s3?
        if len(options.aws_bucket_name) > 0:
            s3_upload_file(options.outputfile, options.aws_bucket_name, options.aws_document_key_name)

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

    # CIDR whitelist as a line separted list of 8.8.8.0/24 style masks
    options.network_list_file = getConfig('network_whitelist_file', '', options.configfile)
    options.ipwhitelist = parse_network_whitelist(options.network_list_file)

    # Output File Name
    options.outputfile = getConfig('outputfile', 'ipblocklist.txt', options.configfile)

    # Days after expiration that we purge an ipblocklist entry (from the ui, they don't end up in the export after expiring)
    options.expireage = getConfig('expireage', 1, options.configfile)

    # Max IPs to emit
    options.iplimit = getConfig('iplimit', 1000, options.configfile)

    # AWS creds
    options.aws_access_key_id = getConfig('aws_access_key_id', '', options.configfile)  # aws credentials to use to connect to mozilla_infosec_blocklist
    options.aws_secret_access_key = getConfig('aws_secret_access_key', '', options.configfile)
    options.aws_bucket_name = getConfig('aws_bucket_name', '', options.configfile)
    options.aws_document_key_name = getConfig('aws_document_key_name', '', options.configfile)


def s3_upload_file(file_path, bucket_name, key_name):
    """
    Upload a file to the given s3 bucket and return a template url.
    """
    s3 = boto3.resource(
        's3',
        aws_access_key_id=options.aws_access_key_id,
        aws_secret_access_key=options.aws_secret_access_key
    )
    s3.meta.client.upload_file(
        file_path, bucket_name, key_name, ExtraArgs={'ACL': 'public-read'})
    url = "https://s3.amazonaws.com/{}/{}".format(bucket_name, key_name)
    print("URL: {}".format(url))
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
    main()
