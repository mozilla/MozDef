#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# Copyright (c) 2014 Mozilla Corporation

# Snapshot configured backups
# Meant to be run once/day
# Each run creates a snapshot of indexname-epochtimestamp
# .conf file will determine what indexes are operated on
# Create a starter .conf file with backupDiscover.py
# You must create the s3 bucket (options.aws_bucket) first paying attention to
# the region assigned to the bucket.
# Snapshots will be placed in:
# options.aws_bucket/elasticsearch/YYYY-MM/servername/indices/indexname

import sys
from datetime import datetime
from datetime import timedelta
from datetime import date
from configlib import getConfig, OptionParser
import calendar
import socket
import requests
import json
from mozdef_util.utilities.logger import logger


def main():
    logger.debug('started')

    json_headers = {
        'Content-Type': 'application/json',
    }
    try:
        esserver = options.esservers[0]
        idate = date.strftime(datetime.utcnow() - timedelta(days=1), '%Y%m%d')
        bucketdate = date.strftime(datetime.utcnow() - timedelta(days=1), '%Y-%m')
        hostname = socket.gethostname()

        # Create or update snapshot configuration
        logger.debug('Configuring snapshot repository')
        snapshot_config = {
            "type": "s3",
            "settings": {
                "bucket": options.aws_bucket,
                "base_path": "elasticsearch/{0}/{1}".format(bucketdate, hostname)
            }
        }
        r = requests.put('%s/_snapshot/s3backup' % esserver, headers=json_headers, data=json.dumps(snapshot_config))
        if 'status' in r.json():
            logger.error("Error while registering snapshot repo: %s" % r.text)
        else:
            logger.debug('snapshot repo registered')

        # do the actual snapshotting
        for (index, dobackup, rotation, pruning) in zip(options.indices, options.dobackup, options.rotation, options.pruning):
            if dobackup == '1':
                index_to_snapshot = index
                if rotation == 'daily':
                    index_to_snapshot += '-%s' % idate
                elif rotation == 'monthly':
                    index_to_snapshot += '-%s' % idate[:6]

                logger.debug('Creating %s snapshot (this may take a while)...' % index_to_snapshot)
                snapshot_config = {
                    'indices': index_to_snapshot
                }
                epoch = calendar.timegm(datetime.utcnow().utctimetuple())
                r = requests.put(
                    '{0}/_snapshot/s3backup/{1}-{2}?wait_for_completion=true'.format(esserver, index_to_snapshot, epoch),
                    headers=json_headers,
                    data=json.dumps(snapshot_config)
                )
                if 'status' in r.json():
                    logger.error('Error snapshotting %s: %s' % (index_to_snapshot, r.json()))
                else:
                    logger.debug('snapshot %s finished' % index_to_snapshot)

    except Exception as e:
        logger.error("Unhandled exception, terminating: %r" % e)


def initConfig():
    # output our log to stdout or syslog
    options.output = getConfig(
        'output',
        'stdout',
        options.configfile
    )
    # syslog hostname
    options.sysloghostname = getConfig(
        'sysloghostname',
        'localhost',
        options.configfile
    )
    options.syslogport = getConfig(
        'syslogport',
        514,
        options.configfile
    )
    options.esservers = list(getConfig(
        'esservers',
        'http://localhost:9200',
        options.configfile).split(',')
    )
    options.indices = list(getConfig(
        'backup_indices',
        'events,alerts,.kibana',
        options.configfile).split(',')
    )
    options.dobackup = list(getConfig(
        'backup_dobackup',
        '1,1,1',
        options.configfile).split(',')
    )
    options.rotation = list(getConfig(
        'backup_rotation',
        'daily,monthly,none',
        options.configfile).split(',')
    )
    options.pruning = list(getConfig(
        'backup_pruning',
        '20,0,0',
        options.configfile).split(',')
    )
    options.aws_bucket = getConfig(
        'aws_bucket',
        '',
        options.configfile
    )


if __name__ == '__main__':
    parser = OptionParser()
    defaultconfigfile = sys.argv[0].replace('.py', '.conf')
    parser.add_option("-c",
                      dest='configfile',
                      default=defaultconfigfile,
                      help="configuration file to use")
    (options, args) = parser.parse_args()
    initConfig()
    main()
