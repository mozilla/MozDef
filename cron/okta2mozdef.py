#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# Copyright (c) 2014 Mozilla Corporation

import sys
from configlib import getConfig, OptionParser
import json
from datetime import datetime
import requests
import netaddr

from mozdef_util.utilities.logger import logger
from mozdef_util.utilities.toUTC import toUTC
from mozdef_util.elasticsearch_client import ElasticsearchClient


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
            json.dump(
                self.data,
                f,
                sort_keys=True,
                indent=4,
                separators=(',', ': ')
            )


def main():
    logger.debug('started')
    # logger.debug(options)
    try:
        es = ElasticsearchClient((list('{0}'.format(s) for s in options.esservers)))
        s = requests.Session()
        s.headers.update({'Accept': 'application/json'})
        s.headers.update({'Content-type': 'application/json'})
        s.headers.update({'Authorization': 'SSWS {0}'.format(options.apikey)})

        # capture the time we start running so next time we catch any events created while we run.
        state = State(options.state_file)
        lastrun = toUTC(datetime.now()).isoformat()

        r = s.get('https://{0}/api/v1/events?startDate={1}&limit={2}'.format(
            options.oktadomain,
            toUTC(state.data['lastrun']).strftime('%Y-%m-%dT%H:%M:%S.000Z'),
            options.recordlimit
        ))

        if r.status_code == 200:
            oktaevents = json.loads(r.text)
            for event in oktaevents:
                if 'published' in event:
                    if toUTC(event['published']) > toUTC(state.data['lastrun']):
                        try:
                            mozdefEvent = dict()
                            mozdefEvent['utctimestamp']=toUTC(event['published']).isoformat()
                            mozdefEvent['receivedtimestamp']=toUTC(datetime.now()).isoformat()
                            mozdefEvent['category'] = 'okta'
                            mozdefEvent['tags'] = ['okta']
                            if 'action' in event and 'message' in event['action']:
                                mozdefEvent['summary'] = event['action']['message']
                            mozdefEvent['details'] = event
                            # Actor parsing
                            # While there are various objectTypes attributes, we just take any attribute that matches
                            # in case Okta changes it's structure around a bit
                            # This means the last instance of each attribute in all actors will be recorded in mozdef
                            # while others will be discarded
                            # Which ends up working out well in Okta's case.
                            if 'actors' in event:
                                for actor in event['actors']:
                                    if 'ipAddress' in actor:
                                        if netaddr.valid_ipv4(actor['ipAddress']):
                                            mozdefEvent['details']['sourceipaddress'] = actor['ipAddress']
                                    if 'login' in actor:
                                        mozdefEvent['details']['username'] = actor['login']
                                    if 'requestUri' in actor:
                                        mozdefEvent['details']['source_uri'] = actor['requestUri']

                            # We are renaming action to activity because there are
                            # currently mapping problems with the details.action field
                            mozdefEvent['details']['activity'] = mozdefEvent['details']['action']
                            mozdefEvent['details'].pop('action')
                            mozdefEvent['type'] = 'okta'

                            jbody=json.dumps(mozdefEvent)
                            res = es.save_event(body=jbody)
                            logger.debug(res)
                        except Exception as e:
                            logger.error('Error handling log record {0} {1}'.format(r, e))
                            continue
                else:
                    logger.error('Okta event does not contain published date: {0}'.format(event))
            state.data['lastrun'] = lastrun
            state.write_state_file()
        else:
            logger.error('Could not get Okta events HTTP error code {} reason {}'.format(r.status_code, r.reason))
    except Exception as e:
        logger.error("Unhandled exception, terminating: %r" % e)


def initConfig():
    options.output=getConfig('output','stdout',options.configfile)  # output our log to stdout or syslog
    options.sysloghostname=getConfig('sysloghostname','localhost',options.configfile)  # syslog hostname
    options.syslogport=getConfig('syslogport',514,options.configfile)  # syslog port
    options.apikey=getConfig('apikey','',options.configfile)  # okta api key to use
    options.oktadomain = getConfig('oktadomain', 'yourdomain.okta.com', options.configfile)  # okta domain: something.okta.com
    options.esservers=list(getConfig('esservers','http://localhost:9200',options.configfile).split(','))
    options.state_file=getConfig('state_file','{0}.json'.format(sys.argv[0]),options.configfile)
    options.recordlimit = getConfig('recordlimit', 10000, options.configfile)  # max number of records to request


if __name__ == '__main__':
    parser=OptionParser()
    parser.add_option("-c", dest='configfile', default=sys.argv[0].replace('.py', '.conf'), help="configuration file to use")
    (options,args) = parser.parse_args()
    initConfig()
    main()
