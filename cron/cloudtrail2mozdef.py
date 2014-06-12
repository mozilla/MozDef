#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
# Copyright (c) 2014 Mozilla Corporation
#
# Contributors:
# Jeff Bryner jbryner@mozilla.com

import os
import sys
from configlib import getConfig,OptionParser,setConfig
import logging
from logging.handlers import SysLogHandler
import boto
import gzip
from StringIO import StringIO
import json
import time
import pyes
from datetime import datetime
from datetime import timedelta
from dateutil.parser import parse
from datetime import date
import pytz

logger = logging.getLogger(sys.argv[0])
logger.level=logging.INFO
formatter = logging.Formatter('%(asctime)s %(name)s %(levelname)s %(message)s')

def toUTC(suspectedDate,localTimeZone=None):
    '''make a UTC date out of almost anything'''
    utc=pytz.UTC
    objDate=None
    if localTimeZone is None:
        localTimeZone=options.defaultTimeZone
    if type(suspectedDate) in (str,unicode):
        objDate=parse(suspectedDate,fuzzy=True)
    elif type(suspectedDate)==datetime:
        objDate=suspectedDate

    if objDate.tzinfo is None:
        objDate=pytz.timezone(localTimeZone).localize(objDate)
        objDate=utc.normalize(objDate)
    else:
        objDate=utc.normalize(objDate)
    if objDate is not None:
        objDate=utc.normalize(objDate)

    return objDate
def main():
    if options.output=='syslog':
        logger.addHandler(SysLogHandler(address=(options.sysloghostname,options.syslogport)))
    else:
        sh=logging.StreamHandler(sys.stderr)
        sh.setFormatter(formatter)
        logger.addHandler(sh)

    logger.debug('started')
    #logger.debug(options)
    try:
        es=pyes.ES((list('{0}'.format(s) for s in options.esservers)))
        boto.connect_cloudtrail(aws_access_key_id=options.aws_access_key_id,aws_secret_access_key=options.aws_secret_access_key)
        #capture the time we start running so next time we catch any files created while we run.
        lastrun=toUTC(datetime.now()).isoformat()
        #in case we don't archive files..only look at today and yesterday's files.
        yesterday=date.strftime(datetime.utcnow()-timedelta(days=1),'%Y/%m/%d')
        today = date.strftime(datetime.utcnow(),'%Y/%m/%d')
        for region in boto.cloudtrail.regions():
            logger.debug('connecting to AWS region {0}'.format(region.name))
            ct=boto.cloudtrail.connect_to_region(region.name,aws_access_key_id=options.aws_access_key_id,aws_secret_access_key=options.aws_secret_access_key)
            trails=ct.describe_trails()['trailList']

            for trail in trails:
                s3 = boto.connect_s3(aws_access_key_id=options.aws_access_key_id,aws_secret_access_key=options.aws_secret_access_key)
                ctbucket=s3.get_bucket(trail['S3BucketName'])
                #ctbucket.get_all_keys()
                filelist=list()
                for bfile in ctbucket.list():

                    if 'CloudTrail' in bfile.key and 'json' in bfile.key:
                        if today in bfile.key or yesterday in bfile.key:
                            filelist.append(bfile.key)
                        else:
                            if options.purge:   #delete old files so we don't try to keep reading them.
                                s3file=ctbucket.get_key(afile)
                                s3file.delete()
                for afile in filelist:
                    s3file=ctbucket.get_key(afile)
                    logger.debug('{0} {1}'.format(afile,s3file.last_modified))

                    if toUTC(s3file.last_modified)>options.lastrun:
                        compressedData=s3file.read()
                        databuf=StringIO(compressedData)
                        f=gzip.GzipFile(fileobj=databuf)
                        jlog=json.loads(f.read())
                        try:
                            for r in jlog['Records']:
                                r['utctimestamp']=toUTC(r['eventTime']).isoformat()
                                jbody=json.dumps(r)
                                res=es.index(index='events',doc_type='cloudtrail',doc=jbody)
                                #logger.debug(res)
                        except Exception as e:
                            logger.error('Error handling log record {0} {1}'.format(r, e))
                            continue
            setConfig('lastrun',lastrun,options.configfile)
    except boto.exception.NoAuthHandlerFound:
        logger.error("No auth handler found, check your credentials")
    except Exception as e:
        logger.error("Unhandled exception, terminating: %r"%e)


def initConfig():
    options.output=getConfig('output','stdout',options.configfile)                      #output our log to stdout or syslog
    options.sysloghostname=getConfig('sysloghostname','localhost',options.configfile)   #syslog hostname
    options.syslogport=getConfig('syslogport',514,options.configfile)                   #syslog port
    options.defaultTimeZone=getConfig('defaulttimezone','US/Pacific',options.configfile)
    options.aws_access_key_id=getConfig('aws_access_key_id','',options.configfile)          #aws credentials to use to connect to cloudtrail
    options.aws_secret_access_key=getConfig('aws_secret_access_key','',options.configfile)
    options.esservers=list(getConfig('esservers','http://localhost:9200',options.configfile).split(','))
    options.lastrun=toUTC(getConfig('lastrun',toUTC(datetime.now()-timedelta(hours=1)),options.configfile))
    options.purge=getConfig('purge',False,options.configfile)

if __name__ == '__main__':
    parser=OptionParser()
    parser.add_option("-c", dest='configfile' , default='{0}.conf'.format(sys.argv[0]), help="configuration file to use")
    (options,args) = parser.parse_args()
    initConfig()
    main()
