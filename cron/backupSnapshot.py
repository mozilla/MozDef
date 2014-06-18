#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
# Copyright (c) 2014 Mozilla Corporation
#
# Contributors:
# Anthony Verez averez@mozilla.com

# Snapshot configured backups

import sys
import os
import logging
from logging.handlers import SysLogHandler
from datetime import datetime
from datetime import timedelta
from datetime import date
from configlib import getConfig, OptionParser, setConfig
import socket
import boto
import boto.s3
import requests
import json
from os.path import expanduser

logger = logging.getLogger(sys.argv[0])
logger.level=logging.INFO
formatter = logging.Formatter('%(asctime)s %(name)s %(levelname)s %(message)s')


def main():
    if options.output == 'syslog':
        logger.addHandler(SysLogHandler(address=(options.sysloghostname, options.syslogport)))
    else:
        sh = logging.StreamHandler(sys.stderr)
        sh.setFormatter(formatter)
        logger.addHandler(sh)

    logger.debug('started')
    try:
        esserver = options.esservers[0]
        s3 = boto.connect_s3(
            aws_access_key_id=options.aws_access_key_id,
            aws_secret_access_key=options.aws_secret_access_key
        )
        idate = date.strftime(datetime.utcnow()-timedelta(days=1),'%Y%m%d')
        yearmonth = date.strftime(datetime.utcnow()-timedelta(days=1),'%Y-%m')
        hostname = socket.gethostname()

        # Create snapshot repo if not registered
        r = requests.get('%s/_snapshot/s3backup2' % esserver)
        if r.json().has_key('status') and r.json()['status'] == 404:
            logger.debug('Configuring snapshot repository (first time run only)...')
            snapshot_config = {
                "type": "s3",
                "settings": {
                    "bucket": "mozdefesbackups",
                    "base_path": "elasticsearch/%s" % hostname,
                    "region": "us-west"
                }
            }
            r = requests.put('%s/_snapshot/s3backup2' % esserver, data=json.dumps(snapshot_config))
            if r.json().has_key('status'):
                logger.error("Error while registering snapshot repo: %s" % r.text)
            else:
                logger.debug('snapshot repo registered')

        # do the actual snapshotting
        for (index, dobackup, rotation, pruning) in zip(options.indices,
            options.dobackup, options.rotation, options.pruning):
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
                # register snapshots to myindex-YYYYMMDD even for monthly rotated indices
                r = requests.put('%s/_snapshot/s3backup2/%s-%s?wait_for_completion=true' % (esserver, index, idate),
                    data=json.dumps(snapshot_config))
                if r.json().has_key('status'):
                    logger.error('Error snapshotting %s: %s' % (index_to_snapshot, r.json()))
                else:
                    logger.debug('snapshot %s finished' % index_to_snapshot)

                # create a restore script
                localpath = '%s/%s-restore.sh' % (expanduser("~"), index)

                with open(localpath, 'w') as f:
                    logger.debug('Writing %s' % localpath)
                    f.write("""
#!/bin/bash

echo -n "Restoring the snapshot..."
curl -s -XPOST "%s/_snapshot/s3backup2/%s-%s/_restore?wait_for_completion=true"

echo "DONE!"
                    """ % (esserver, index, idate))

                # upload the restore script
                bucket = s3.get_bucket('mozdefesbackups')
                key = bucket.new_key('elasticsearch/%s/%s-%s-restore.sh' % (
                    hostname, index, idate))
                key.set_contents_from_filename(localpath)

                # removing local file
                os.remove(localpath)

    except boto.exception.NoAuthHandlerFound:
        logger.error("No auth handler found, check your credentials")
    except Exception as e:
        logger.error("Unhandled exception, terminating: %r"%e)

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
        'events,alerts,kibana-int',
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
    # aws credentials to use to send files to s3
    options.aws_access_key_id = getConfig(
        'aws_access_key_id',
        '',
        options.configfile
        )
    options.aws_secret_access_key = getConfig(
        'aws_secret_access_key',
        '',
        options.configfile
        )

if __name__ == '__main__':
    parser = OptionParser()
    defaultconfigfile = sys.argv[0].replace('backupSnapshot.py', 'backup.conf')
    parser.add_option("-c",
                      dest='configfile',
                      default=defaultconfigfile,
                      help="configuration file to use")
    (options, args) = parser.parse_args()
    initConfig()
    main()
