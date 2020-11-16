#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# Copyright (c) 2014 Mozilla Corporation

import sys
import json
from configlib import getConfig, OptionParser
from datetime import datetime
from google.oauth2 import service_account
import googleapiclient.discovery
import mozdef_client as mozdef
from mozdef_util.utilities.toUTC import toUTC
from mozdef_util.utilities.logger import logger


class State:
    def __init__(self, filename):
        '''Set the filename and populate self.data by calling self.read_stat_file()'''
        self.filename = filename
        self.read_state_file()

    def read_state_file(self):
        '''Populate self.data by reading and parsing the state file'''
        try:
            with open(self.filename, 'r') as f:
                self.data = json.load(f)
        except IOError:
            self.data = {}
        except ValueError:
            logger.error("%s state file found but isn't a recognized json format" % self.filename)
            raise
        except TypeError:
            logger.error("%s state file found and parsed but it doesn't contain an iterable object" % self.filename)
            raise

    def write_state_file(self):
        '''Write the self.data value into the state file'''
        with open(self.filename, 'w') as f:
            json.dump(self.data, f, sort_keys=True, indent=4, separators=(',', ': '))


def flattenDict(inDict, pre=None, values=True):
    '''given a dictionary, potentially with multiple sub dictionaries
       return a period delimited version of the dict with or without values
       i.e. {'something':'value'} becomes something=value
            {'something':{'else':'value'}} becomes something.else=value
    '''
    pre = pre[:] if pre else []
    if isinstance(inDict, dict):
        for key, value in inDict.items():
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
                        elif value is None:
                            yield '.'.join(pre) + '.' + key + '=None'
                    else:
                        yield '.'.join(pre) + '.' + key
                else:
                    if values:
                        if isinstance(value, str):
                            yield key + '=' + str(value)
                        elif value is None:
                            yield key + '=None'
                    else:
                        yield key
    else:
        yield '-'.join(pre) + '.' + inDict


def main():
    logger.debug('started')
    state = State(options.state_file_name)
    try:
        # capture the time we start running so next time we catch any events
        # created while we run.
        lastrun=toUTC(datetime.now()).isoformat()

        scope=[
            'https://www.googleapis.com/auth/admin.reports.audit.readonly',
            'https://www.googleapis.com/auth/admin.reports.usage.readonly'
        ]

        # get our credentials
        credentials = service_account.Credentials.from_service_account_file(
            options.jsoncredentialfile,
            scopes=scope,
            subject=options.impersonate
        )

        # build a request to the admin sdk
        api = googleapiclient.discovery.build('admin', 'reports_v1', credentials=credentials)
        response = api.activities().list(userKey='all',
                                         applicationName='login',
                                         startTime=toUTC(state.data['lastrun']).strftime('%Y-%m-%dT%H:%M:%S.000Z'),
                                         maxResults=options.recordlimit).execute()

        # fix up the event craziness to a flatter format
        events=[]
        if 'items' in response:
            for i in response['items']:
                # flatten the sub dict/lists to pull out the good parts
                mozmsg = mozdef.MozDefEvent(options.url)
                mozmsg.category = 'google'
                mozmsg.tags = ['google','authentication']
                mozmsg.severity = 'INFO'
                mozmsg.summary = 'google authentication: '

                details=dict()
                for keyValue in flattenDict(i):
                    # change key/values like:
                    # actor.email=someone@mozilla.com
                    # to actor_email=value
                    try:
                        key,value =keyValue.split('=')
                    except ValueError as e:
                        continue
                    key=key.replace('.','_').lower()
                    details[key]=value

                # find important keys
                # and adjust their location/name
                if 'ipaddress' in details:
                    # it's the source ip
                    details['sourceipaddress']=details['ipaddress']
                    del details['ipaddress']

                if 'id_time' in details:
                    mozmsg.timestamp = details['id_time']
                    mozmsg.utctimestamp = details['id_time']
                if 'events_name' in details:
                    mozmsg.summary += details['events_name'] + ' '
                if 'actor_email' in details:
                    mozmsg.summary += details['actor_email'] + ' '

                mozmsg.details = details
                events.append(mozmsg)

        # post events to mozdef
        logger.debug('posting {0} google events to mozdef'.format(len(events)))
        for e in events:
            e.send()

        # record the time we started as
        # the start time for next time.
        state.data['lastrun'] = lastrun
        state.write_state_file()
    except Exception as e:
        logger.error("Unhandled exception, terminating: %r" % e)


def initConfig():
    options.output=getConfig('output','stdout',options.configfile)  # output our log to stdout or syslog
    options.sysloghostname=getConfig('sysloghostname','localhost',options.configfile)  # syslog hostname
    options.syslogport=getConfig('syslogport',514,options.configfile)  # syslog port
    options.url = getConfig('url', 'http://localhost:8080/events', options.configfile)  # mozdef event input url to post to
    options.state_file_name = getConfig('state_file_name','{0}.state'.format(sys.argv[0]),options.configfile)
    options.recordlimit = getConfig('recordlimit', 1000, options.configfile)  # max number of records to request
    #
    # See
    # https://developers.google.com/admin-sdk/reports/v1/guides/delegation
    # for detailed information on delegating a service account for use in gathering google admin sdk reports
    #

    # google's json credential file exported from the project/admin console
    options.jsoncredentialfile=getConfig('jsoncredentialfile','/path/to/filename.json',options.configfile)

    # email of admin to impersonate as a service account
    options.impersonate = getConfig('impersonate', 'someone@yourcompany.com', options.configfile)


if __name__ == '__main__':
    parser=OptionParser()
    parser.add_option("-c", dest='configfile', default=sys.argv[0].replace('.py', '.conf'), help="configuration file to use")
    (options,args) = parser.parse_args()
    initConfig()
    main()
