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
import json
from configlib import getConfig, OptionParser
from datetime import datetime
from dateutil.parser import parse
from logging.handlers import SysLogHandler
import boto.sqs
from boto.sqs.message import RawMessage
from pytx.access_token import access_token
from pytx import ThreatIndicator
from pytx.vocabulary import ThreatIndicator as td

import sys
import os
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../lib'))
from utilities.toUTC import toUTC

logger = logging.getLogger(sys.argv[0])
logger.level = logging.INFO
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
    if options.output == 'syslog':
        logger.addHandler(SysLogHandler(address=(options.sysloghostname, options.syslogport)))
    else:
        sh = logging.StreamHandler(sys.stderr)
        sh.setFormatter(formatter)
        logger.addHandler(sh)

    logger.debug('started')

    # set up SQS
    conn = boto.sqs.connect_to_region(options.region,
                                      aws_access_key_id=options.aws_access_key_id,
                                      aws_secret_access_key=options.aws_secret_access_key)
    queue = conn.get_queue(options.aws_queue_name)

    state = State(options.state_file_name)
    try:
        access_token(options.appid, options.appsecret)
        # capture the time we start running so next time we catch any events
        # created while we run.
        lastrun = toUTC(datetime.now()).isoformat()

        queryDict = {}
        queryDict['since'] = parse(state.data['lastrun']).isoformat()
        queryDict['until'] = lastrun

        logger.debug('Querying {0}'.format(queryDict))

        results = ThreatIndicator.objects(
            type_='COMPROMISED_CREDENTIAL',
            since=queryDict['since'],
            until=queryDict['until']
        )
        email_indicators = []
        for result in results:
            indicator_str = result.get(td.INDICATOR)
            indicators = indicator_str.split(':')
            email_address = indicators[0]
            print email_address
            email_indicators.append(email_address)

        # send the results to SQS
        for indicator in email_indicators:
            sendToCustomsServer(queue, indicator)

        # record the time we started as
        # the start time for next time.
        state.data['lastrun'] = lastrun
        state.write_state_file()
    except Exception as e:
        logger.error("Unhandled exception, terminating: %r" % e)

    logger.debug('finished')


def initConfig():
    options.output = getConfig('output', 'stdout', options.configfile)
    options.sysloghostname = getConfig('sysloghostname', 'localhost', options.configfile)
    options.syslogport = getConfig('syslogport', 514, options.configfile)
    options.mozdefurl = getConfig('url', 'http://localhost:8080/events', options.configfile)
    options.state_file_name = getConfig('state_file_name', '{0}.state'.format(sys.argv[0]), options.configfile)
    options.recordlimit = getConfig('recordlimit', 1000, options.configfile)

    # threat exchange options
    options.appid = getConfig('appid', '', options.configfile)
    options.appsecret = getConfig('appsecret', '', options.configfile)

    # boto options
    options.region = getConfig('region', 'us-west-2', options.configfile)
    options.aws_access_key_id = getConfig('aws_access_key_id', '', options.configfile)
    options.aws_secret_access_key = getConfig('aws_secret_access_key', '', options.configfile)
    options.aws_queue_name = getConfig('aws_queue_name', '', options.configfile)


if __name__ == '__main__':
    parser = OptionParser()
    parser.add_option("-c", dest='configfile', default=sys.argv[0].replace('.py', '.conf'), help="configuration file to use")
    (options, args) = parser.parse_args()
    initConfig()
    main()
