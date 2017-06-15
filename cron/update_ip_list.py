#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
# Copyright (c) 2017 Mozilla Corporation
#
# Contributors:
# Brandon Myers bmyers@mozilla.com

import sys
import os
from configlib import getConfig, OptionParser
import boto

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../lib'))
from utilities.logger import logger, initLogger


def fetch_ip_list(aws_key_id, aws_secret_key, s3_bucket, ip_list_filename):
    logger.debug("Fetching ip list from s3")
    s3 = boto.connect_s3(
        aws_access_key_id=aws_key_id,
        aws_secret_access_key=aws_secret_key
    )
    bucket = s3.get_bucket(s3_bucket)
    ip_list_key = bucket.lookup(ip_list_filename)
    contents = ip_list_key.get_contents_as_string().rstrip()
    return contents.split("\n")

def save_ip_list(save_path, ips):
    ip_list_contents = '\n'.join(ips)
    logger.debug("Saving ip list")
    if os.path.isfile(save_path):
        logger.debug("Overwriting ip list file in " + str(save_path))
    else:
        logger.debug("Creating new ip list file at " + str(save_path))
    with open(save_path, "w+") as text_file:
        text_file.write(ip_list_contents)

def main():
    logger.debug('Starting')
    logger.debug(options)
    ips = fetch_ip_list(options.aws_access_key_id, options.aws_secret_access_key, options.aws_bucket_name, options.aws_document_key_name)
    if len(ips) < options.ips_list_threshold:
        raise LookupError('IP List contains less than ' + str(options.ips_list_threshold) + ' entries...something is probably up here.')
    save_ip_list(options.local_ip_list_path, ips)

def initConfig():
    # output our log to stdout or syslog
    options.output = getConfig('output', 'stdout', options.configfile)
    options.sysloghostname = getConfig('sysloghostname', 'localhost', options.configfile)
    options.syslogport = getConfig('syslogport', 514, options.configfile)

    options.aws_access_key_id=getConfig('aws_access_key_id','',options.configfile)
    options.aws_secret_access_key=getConfig('aws_secret_access_key','',options.configfile)
    options.aws_bucket_name=getConfig('aws_bucket_name','',options.configfile)
    options.aws_document_key_name=getConfig('aws_document_key_name','',options.configfile)

    options.local_ip_list_path = getConfig('local_ip_list_path', '', options.configfile)
    options.ips_list_threshold = getConfig('ips_list_threshold', 20, options.configfile)


if __name__ == '__main__':
    parser = OptionParser()
    parser.add_option(
        "-c",
        dest='configfile',
        default=sys.argv[0].replace('.py', '.conf'),
        help="configuration file to use")
    (options, args) = parser.parse_args()
    initConfig()
    initLogger(options)
    main()
