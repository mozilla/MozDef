#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# Copyright (c) 2014 Mozilla Corporation
import boto3
import logging
import random
import re
import sys
from datetime import datetime
from datetime import timedelta
from configlib import getConfig, OptionParser
from logging.handlers import SysLogHandler
from pymongo import MongoClient

from mozdef_util.utilities.toUTC import toUTC


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


def genMeteorID():
    return('%024x' % random.randrange(16**24))


def isFQDN(fqdn):
    try:
        # We could resolve FQDNs here, but that could tip our hand and it's
        # possible us investigating could trigger other alerts.
        # validate using the regex from https://github.com/yolothreat/utilitybelt
        fqdn_re = re.compile(r'(?=^.{4,255}$)(^((?!-)[a-zA-Z0-9-]{1,63}(?<!-)\.)+[a-zA-Z]{2,63}$)', re.I | re.S | re.M)
        return bool(re.match(fqdn_re,fqdn))
    except:
        return False


def parse_fqdn_whitelist(fqdn_whitelist_location):
    fqdns = []
    with open(fqdn_whitelist_location, "r") as text_file:
        for line in text_file:
            line = line.strip().strip("'").strip('"')
            if isFQDN(line):
                fqdns.append(line)
    return fqdns


def main():
    logger.debug('starting')
    logger.debug(options)
    try:
        # connect to mongo
        client = MongoClient(options.mongohost, options.mongoport)
        mozdefdb = client.meteor
        fqdnblocklist = mozdefdb['fqdnblocklist']
        # ensure indexes
        fqdnblocklist.create_index([('dateExpiring', -1)])

        # delete any that expired
        fqdnblocklist.delete_many({'dateExpiring': {"$lte": datetime.utcnow() - timedelta(days=options.expireage)}})

        # Lastly, export the combined blocklist
        fqdnCursor = mozdefdb['fqdnblocklist'].aggregate([
            {"$sort": {"dateAdded": -1}},
            {"$match": {"address": {"$exists": True}}},
            {"$match": {
                "$or": [
                    {"dateExpiring": {"$gte": datetime.utcnow()}},
                    {"dateExpiring": {"$exists": False}},
                ]},
             },
            {"$project": {"address": 1}},
            {"$limit": options.fqdnlimit}
        ])
        FQDNList = []
        for fqdn in fqdnCursor:
            if fqdn not in options.fqdnwhitelist:
                FQDNList.append(fqdn['address'])
        # to text
        with open(options.outputfile, 'w') as outputfile:
            for fqdn in FQDNList:
                outputfile.write("{0}\n".format(fqdn))
        outputfile.close()
        # to s3?
        if len(options.aws_bucket_name) > 0:
            s3_upload_file(options.outputfile, options.aws_bucket_name, options.aws_document_key_name)

    except ValueError as e:
        logger.error("Exception %r generating FQDN block list" % e)


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

    # FQDN whitelist as a \n separted file of example.com or foo.bar.com style names
    options.fqdn_whitelist_file = getConfig('fqdn_whitelist_file', '/dev/null', options.configfile)
    options.fqdnwhitelist = parse_fqdn_whitelist(options.fqdn_whitelist_file)

    # Output File Name
    options.outputfile = getConfig('outputfile', 'fqdnblocklist.txt', options.configfile)

    # Days after expiration that we purge an fqdnblocklist entry (from the ui, they don't end up in the export after expiring)
    options.expireage = getConfig('expireage', 1, options.configfile)

    # Max FQDNs to emit
    options.fqdnlimit = getConfig('fqdnlimit', 1000, options.configfile)

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
    initLogger()
    main()
