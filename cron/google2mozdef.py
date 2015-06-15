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
import logging
import pytz
import requests
import json
import time
from configlib import getConfig,OptionParser,setConfig
from datetime import datetime
from datetime import timedelta
from dateutil.parser import parse
from datetime import date
from logging.handlers import SysLogHandler
from httplib2 import Http
from oauth2client.client import SignedJwtAssertionCredentials
from apiclient.discovery import build


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


def flattenDict(inDict, pre=None, values=True):
    '''given a dictionary, potentially with multiple sub dictionaries
       return a period delimited version of the dict with or without values
       i.e. {'something':'value'} becomes something=value
            {'something':{'else':'value'}} becomes something.else=value
    '''
    pre = pre[:] if pre else []
    if isinstance(inDict, dict):
        for key, value in inDict.iteritems():
            if isinstance(value, dict):
                for d in flattenDict(value, pre + [key], values):
                    yield d
            if isinstance(value,list):
                for listItem in value:
                    for i in flattenDict(listItem,pre + [key],values):
                        yield i
            else:
                if pre:
                    if values:
                        if isinstance(value, str):
                            yield '.'.join(pre) + '.' + key + '=' + str(value)
                        elif isinstance(value, unicode):
                            yield '.'.join(pre) + '.' + key + '=' + value.encode('ascii', 'ignore')
                        elif value is None:
                            yield '.'.join(pre) + '.' + key + '=None'
                    else:
                        yield '.'.join(pre) + '.' + key
                else:
                    if values:
                        if isinstance(value, str):
                            yield key + '=' + str(value)
                        elif isinstance(value, unicode):
                            yield key + '=' + value.encode('ascii', 'ignore')
                        elif value is None:
                            yield key + '=None'
                    else:
                        yield key
    else:
        yield '-'.join(pre) + '.' + inDict


def main():
    if options.output=='syslog':
        logger.addHandler(SysLogHandler(address=(options.sysloghostname,options.syslogport)))
    else:
        sh=logging.StreamHandler(sys.stderr)
        sh.setFormatter(formatter)
        logger.addHandler(sh)

    logger.debug('started')

    try:
        # capture the time we start running so next time we catch any events
        # created while we run.
        lastrun=toUTC(datetime.now()).isoformat()

        # get our credentials
        mozdefClient=json.loads(open(options.jsoncredentialfile).read())
        client_email = mozdefClient['client_email']
        private_key=mozdefClient['private_key']

        # set the oauth scope we will request
        scope=[
            'https://www.googleapis.com/auth/admin.reports.audit.readonly',
            'https://www.googleapis.com/auth/admin.reports.usage.readonly'
        ]

        # authorize our http object
        # we do this as a 'service account' so it's important
        # to specify the correct 'sub' option
        # or you will get access denied even with correct delegations/scope

        credentials = SignedJwtAssertionCredentials(client_email,
                                                    private_key,
                                                    scope=scope,
                                                    sub=options.impersonate)
        http = Http()
        credentials.authorize(http)

        # build a request to the admin sdk
        api = build('admin', 'reports_v1', http=http)
        response = api.activities().list(userKey='all',
                                         applicationName='login',
                                         startTime=toUTC(options.lastrun).strftime('%Y-%m-%dT%H:%M:%S.000Z'),
                                         maxResults=options.recordlimit).execute()

        # fix up the event craziness to a flatter format
        events=[]
        if 'items' in response.keys():
            for i in response['items']:
                # flatten the sub dict/lists to pull out the good parts
                event=dict(category='google')
                event['tags']=['google','authentication']
                event['severity']='INFO'
                event['summary']='google authentication: '

                details=dict()
                for keyValue in flattenDict(i):
                    # change key/values like:
                    # actor.email=someone@mozilla.com
                    # to actor_email=value

                    key,value =keyValue.split('=')
                    key=key.replace('.','_').lower()
                    details[key]=value

                # find important keys
                # and adjust their location/name
                if 'ipaddress' in details.keys():
                    # it's the source ip
                    details['sourceipaddress']=details['ipaddress']
                    del details['ipaddress']

                if 'id_time' in details.keys():
                    event['timestamp']=details['id_time']
                    event['utctimestamp']=details['id_time']
                if 'events_name' in details.keys():
                    event['summary']+= details['events_name'] + ' '
                if 'actor_email' in details.keys():
                    event['summary']+= details['actor_email'] + ' '

                event['details']=details
                events.append(event)

        # post events to mozdef
        logger.debug('posting {0} google events to mozdef'.format(len(events)))
        for e in events:
            requests.post(options.url,data=json.dumps(e))

        # record the time we started as
        # the start time for next time.
        setConfig('lastrun',lastrun,options.configfile)
    except Exception as e:
        logger.error("Unhandled exception, terminating: %r"%e)


def initConfig():
    options.output=getConfig('output','stdout',options.configfile)                              #output our log to stdout or syslog
    options.sysloghostname=getConfig('sysloghostname','localhost',options.configfile)           #syslog hostname
    options.syslogport=getConfig('syslogport',514,options.configfile)                           #syslog port
    options.defaultTimeZone=getConfig('defaulttimezone','US/Pacific',options.configfile)        #default timezone
    options.url = getConfig('url', 'http://localhost:8080/events', options.configfile)                  #mozdef event input url to post to
    options.lastrun=toUTC(getConfig('lastrun',toUTC(datetime.now()-timedelta(hours=24)),options.configfile))
    options.recordlimit = getConfig('recordlimit', 1000, options.configfile)                    #max number of records to request
    #
    # See
    # https://developers.google.com/admin-sdk/reports/v1/guides/delegation
    # for detailed information on delegating a service account for use in gathering google admin sdk reports
    #

    #google's json credential file exported from the project/admin console
    options.jsoncredentialfile=getConfig('jsoncredentialfile','/path/to/filename.json',options.configfile)

    #email of admin to impersonate as a service account
    options.impersonate = getConfig('impersonate', 'someone@yourcompany.com', options.configfile)


if __name__ == '__main__':
    parser=OptionParser()
    parser.add_option("-c", dest='configfile' , default=sys.argv[0].replace('.py', '.conf'), help="configuration file to use")
    (options,args) = parser.parse_args()
    initConfig()
    main()
