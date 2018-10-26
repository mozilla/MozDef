#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
# Copyright (c) 2014 Mozilla Corporation

import logging
import random
import sys
from datetime import datetime
from datetime import timedelta
from configlib import getConfig, OptionParser
from logging.handlers import SysLogHandler
from pymongo import MongoClient

import os
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

def main():
    logger.debug('starting')
    logger.debug(options)
    try:
        # connect to mongo
        client = MongoClient(options.mongohost, options.mongoport)
        mozdefdb = client.meteor
        watchlist = mozdefdb['watchlist']

        # delete any that expired
        watchlist.delete_many({'dateExpiring': {"$lte": datetime.utcnow()-timedelta(days=options.expireage)}})

        # Lastly, export the combined watchlist
        watchCursor=mozdefdb['watchlist'].aggregate([
                {"$sort": {"dateAdded": -1}},
                {"$match": {"watchcontent": {"$exists": True}}},
                {"$match":
                    {"$or":[
                        {"dateExpiring": {"$gte": datetime.utcnow()}},
                        {"dateExpiring": {"$exists": False}},
                    ]},
                },
                {"$project":{"watchcontent":1}},
            ])
        WatchList=[]
        for content in watchCursor:
            WatchList.append(content['watchcontent'])
        # to text
        with open(options.outputfile, 'w') as outputfile:
            for content in WatchList:
                outputfile.write("{0}\n".format(content))
        outputfile.close()

    except ValueError as e:
        logger.error("Exception %r generating watch list" % e)


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

    # Output File Name
    options.outputfile = getConfig('outputfile', 'watchlist.txt', options.configfile)

    # Days after expiration that we purge an ipblocklist entry (from the ui, they don't end up in the export after expiring)
    options.expireage = getConfig('expireage',1,options.configfile)

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
