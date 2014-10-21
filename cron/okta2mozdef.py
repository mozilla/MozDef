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
import json
import time
import pyes
from datetime import datetime
from datetime import timedelta
from dateutil.parser import parse
from datetime import date
import pytz
import requests

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
        s = requests.Session()
        s.headers.update({'Accept': 'application/json'})
        s.headers.update({'Content-type': 'application/json'})
        s.headers.update({'Authorization':'SSWS {0}'.format(options.apikey)})
        
        #capture the time we start running so next time we catch any events created while we run.
        lastrun=toUTC(datetime.now()).isoformat()
        #in case we don't archive files..only look at today and yesterday's files.
        yesterday=date.strftime(datetime.utcnow()-timedelta(days=1),'%Y/%m/%d')
        today = date.strftime(datetime.utcnow(),'%Y/%m/%d')
        
        r = s.get('https://{0}/api/v1/events?startDate={1}&limit={2}'.format(
            options.oktadomain,
            toUTC(options.lastrun).strftime('%Y-%m-%dT%H:%M:%S.000Z'),
            options.recordlimit
        ))
        
        if r.status_code == 200:
            oktaevents = json.loads(r.text)
            for event in oktaevents:
                if 'published' in event.keys():
                    if toUTC(event['published'])>options.lastrun:
                        try:
                            mozdefEvent = dict()
                            mozdefEvent['utctimestamp']=toUTC(event['published']).isoformat()
                            mozdefEvent['category'] = 'okta'
                            mozdefEvent['tags'] = ['okta']
                            if 'action' in event.keys() and 'message' in event['action'].keys():
                                mozdefEvent['summary'] = event['action']['message']
                            mozdefEvent['details'] = event
                            jbody=json.dumps(mozdefEvent)
                            res=es.index(index='events',doc_type='okta',doc=jbody)
                            logger.debug(res)
                        except Exception as e:
                            logger.error('Error handling log record {0} {1}'.format(r, e))
                            continue
                else:
                    logger.error('Okta event does not contain published date: {0}'.format(event))
            setConfig('lastrun',lastrun,options.configfile)                            
    except Exception as e:
        logger.error("Unhandled exception, terminating: %r"%e)


def initConfig():
    options.output=getConfig('output','stdout',options.configfile)                              #output our log to stdout or syslog
    options.sysloghostname=getConfig('sysloghostname','localhost',options.configfile)           #syslog hostname
    options.syslogport=getConfig('syslogport',514,options.configfile)                           #syslog port
    options.defaultTimeZone=getConfig('defaulttimezone','US/Pacific',options.configfile)        #default timezone
    options.apikey=getConfig('apikey','',options.configfile)                                    #okta api key to use
    options.oktadomain = getConfig('oktadomain', 'yourdomain.okta.com', options.configfile)     #okta domain: something.okta.com
    options.esservers=list(getConfig('esservers','http://localhost:9200',options.configfile).split(','))
    options.lastrun=toUTC(getConfig('lastrun',toUTC(datetime.now()-timedelta(hours=1)),options.configfile))
    options.recordlimit = getConfig('recordlimit', 10000, options.configfile)                    #max number of records to request
    

if __name__ == '__main__':
    parser=OptionParser()
    parser.add_option("-c", dest='configfile' , default=sys.argv[0].replace('.py', '.conf'), help="configuration file to use")
    (options,args) = parser.parse_args()
    initConfig()
    main()
