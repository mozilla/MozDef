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
import re
from configlib import getConfig, OptionParser
from datetime import datetime
from datetime import timedelta
from dateutil.parser import parse
from datetime import date
from logging.handlers import SysLogHandler
from pytx import init
from pytx import ThreatIndicator
import boto.sqs
from boto.sqs.message import RawMessage
from urllib2 import urlopen
from urllib import urlencode


import sys
import os
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../lib'))
from utilities.toUTC import toUTC

logger = logging.getLogger(sys.argv[0])
logger.level=logging.INFO
formatter = logging.Formatter('%(asctime)s %(name)s %(levelname)s %(message)s')


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


def buildQuery(optionDict):
    '''
    Builds a query string based on the dict of options
    '''
    if optionDict['since'] is None or optionDict['until'] is None:
        logger.error('"since" and "until" are both required')
        raise Exception('You must specify both "since" and "until" values')

    fields = ({
        'access_token' : options.appid + '|' + options.appsecret,
        'threat_type': 'COMPROMISED_CREDENTIAL',
        'type' : 'EMAIL_ADDRESS',
        'fields' : 'indicator,passwords',
        'since' : optionDict['since'],
        'until' : optionDict['until'],
    })

    return options.txserver + 'threat_indicators?' + urlencode(fields)

def executeQuery(url):
    queryResults=[]

    try:
        response = urlopen(url).read()
    except TypeError as e:
        logger.error('Type error %r'%e)
        return queryResults,None
    except Exception as e:
        lines = str(e.info()).split('\r\n')
        msg = str(e)
        for line in lines:
            # get the exact error from the server
            result = re.search('^WWW-Authenticate: .*\) (.*)\"$', line)
            if result:
                msg = result.groups()[0]
        logger.error ('ERROR: %s\nReceived' % (msg))
        return queryResults,None

    try:
        data = json.loads(response)

        if 'data' in data.keys():
            for d in data['data']:
                queryResults.append(dict(email=d['indicator'],md5=d['passwords']))

        if 'paging' in data:
            nextURL=data['paging']['next']
        else:
            nextURL=None

        return queryResults,nextURL

    except Exception as e:
        logger.error('ERROR: %r' % (e))
        return queryResults,None


def sendToCustomsServer(queue, emailAddress=None):
    try:
        if emailAddress is not None:
            # connect and send a message like:
            # '{"Message": {"ban": {"email": "someone@somewhere.com"}}}'
            # encoded like this:
            # {"Message":"{\"ban\":{\"email\":\"someone@somewhere.com\"}}"}

            banMessage = dict(Message=json.dumps(dict(ban=dict(email=emailAddress))))
            m = RawMessage()
            m.set_body(json.dumps(banMessage))
            queue.write(m)
            logger.info('Sent {0} to customs server'.format(emailAddress))

    except Exception as e:
        logger.error('Error while sending to customs server %s: %r' % (emailAddress, e))



def main():
    if options.output=='syslog':
        logger.addHandler(SysLogHandler(address=(options.sysloghostname,options.syslogport)))
    else:
        sh=logging.StreamHandler(sys.stderr)
        sh.setFormatter(formatter)
        logger.addHandler(sh)

    logger.debug('started')

    # set up the threat exchange secret
    init(options.appid, options.appsecret)
    # set up SQS
    conn = boto.sqs.connect_to_region(options.region,
                                      aws_access_key_id=options.aws_access_key_id,
                                      aws_secret_access_key=options.aws_secret_access_key)
    queue = conn.get_queue(options.aws_queue_name)
    state = State(options.state_file_name)
    try:
        # capture the time we start running so next time we catch any events
        # created while we run.
        lastrun=toUTC(datetime.now()).isoformat()

        queryDict = {}
        queryDict['since'] = parse(state.data['lastrun']).isoformat()
        queryDict['until'] = datetime.utcnow().isoformat()

        logger.debug('Querying {0}'.format(queryDict))

        # we get results in pages
        # so iterate through the pages
        # and append to a list
        nextURL=buildQuery(queryDict)
        allResults=[]
        while nextURL is not None:
            results,nextURL=executeQuery(nextURL)
            for r in results:
                allResults.append(r)

        # send the results to SQS
        for r in allResults:
            sendToCustomsServer(queue, r['email'])

        # record the time we started as
        # the start time for next time.
        if len(allResults) > 0:
            state.data['lastrun'] = lastrun
            state.write_state_file()
    except Exception as e:
        logger.error("Unhandled exception, terminating: %r"%e)

    logger.debug('finished')


def initConfig():
    options.output=getConfig('output','stdout',options.configfile)                              #output our log to stdout or syslog
    options.sysloghostname=getConfig('sysloghostname','localhost',options.configfile)           #syslog hostname
    options.syslogport=getConfig('syslogport',514,options.configfile)                           #syslog port
    options.mozdefurl = getConfig('url', 'http://localhost:8080/events', options.configfile)                  #mozdef event input url to post to
    options.state_file_name = getConfig('state_file_name','{0}.state'.format(sys.argv[0]),options.configfile)
    options.recordlimit = getConfig('recordlimit', 1000, options.configfile)                    #max number of records to request

    # threat exchange options
    options.appid = getConfig('appid',
                              '',
                              options.configfile)
    options.appsecret=getConfig('appsecret',
                                '',
                                options.configfile)

    options.txserver = getConfig('txserver',
                                 'https://graph.facebook.com/',
                                 options.configfile)

    # boto options
    options.region = getConfig('region',
                                'us-west-2',
                                options.configfile)
    options.aws_access_key_id=getConfig('aws_access_key_id',
                                        '',
                                        options.configfile)
    options.aws_secret_access_key=getConfig('aws_secret_access_key',
                                            '',
                                            options.configfile)
    options.aws_queue_name=getConfig('aws_queue_name',
                                    '',
                                    options.configfile)


if __name__ == '__main__':
    parser=OptionParser()
    parser.add_option("-c", dest='configfile' , default=sys.argv[0].replace('.py', '.conf'), help="configuration file to use")
    (options,args) = parser.parse_args()
    initConfig()
    main()
