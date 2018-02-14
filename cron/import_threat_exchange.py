#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
# Copyright (c) 2017 Mozilla Corporation

import os
import sys
from configlib import getConfig, OptionParser
from datetime import datetime
from datetime import timedelta

from pytx.access_token import access_token
from pytx import ThreatDescriptor
from pytx import Malware

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../lib'))
from utilities.logger import logger, initLogger
from utilities.toUTC import toUTC
from elasticsearch_client import ElasticsearchClient

from state import State


def pull_threat_exchange_data(type_str, params):
    logger.debug('Querying threat exchange for {}'.format(type_str))
    results = params['threat_class'].objects(**params['query_params'])
    docs = []
    for result in results:
        created_date = toUTC(datetime.now()).isoformat()
        es_doc = {
            'created_on': created_date,
            'details': result
        }
        docs.append(es_doc)
    return docs


def main():
    logger.debug('Connecting to Elasticsearch')
    client = ElasticsearchClient(options.esservers)
    logger.debug('Connecting to threat exchange')
    access_token(options.appid, options.appsecret)
    state = State(options.state_file_name)
    current_timestamp = toUTC(datetime.now()).isoformat()
    # We're setting a default for the past 2 days of data
    # if there isnt a state file
    since_date_obj = toUTC(datetime.now()) - timedelta(days=2)
    since_date = since_date_obj.isoformat()
    if 'lastrun' in state.data.keys():
        since_date = state.data['lastrun']

    # A master dict of all the different types of
    # data we want to pull from threat exchange
    params = {
        'malware_hash': {
            'threat_class': Malware,
            'query_params': {},
        },
        'ip_address': {
            'threat_class': ThreatDescriptor,
            'query_params': {
                'type_': 'IP_ADDRESS',
            }
        },
        'domain': {
            'threat_class': ThreatDescriptor,
            'query_params': {
                'type_': 'DOMAIN',
            }
        },
        'uri': {
            'threat_class': ThreatDescriptor,
            'query_params': {
                'type_': 'URI',
            }
        },
        'debug_string': {
            'threat_class': ThreatDescriptor,
            'query_params': {
                'type_': 'DEBUG_STRING',
            }
        },
        'banner': {
            'threat_class': ThreatDescriptor,
            'query_params': {
                'type_': 'BANNER',
            }
        },
        'email_address': {
            'threat_class': ThreatDescriptor,
            'query_params': {
                'type_': 'EMAIL_ADDRESS',
            }
        },
        'file_created': {
            'threat_class': ThreatDescriptor,
            'query_params': {
                'type_': 'FILE_CREATED',
            }
        },
    }
    docs = {}
    for param_key, param in params.iteritems():
        param['query_params']['since'] = str(since_date)
        param['query_params']['until'] = str(current_timestamp)
        param['query_params']['dict_generator'] = True
        docs = pull_threat_exchange_data(param_key, param)
        logger.debug('Saving {0} {1} to ES'.format(len(docs), param_key))
        for doc in docs:
            client.save_object(index='threat-exchange', doc_type=param_key, body=doc)

    state.data['lastrun'] = current_timestamp
    state.save()


def initConfig():
    options.output = getConfig('output', 'stdout', options.configfile)
    options.sysloghostname = getConfig('sysloghostname', 'localhost', options.configfile)
    options.syslogport = getConfig('syslogport', 514, options.configfile)
    options.state_file_name = getConfig('state_file_name', '{0}.state'.format(sys.argv[0]), options.configfile)
    # threat exchange options
    options.appid = getConfig('appid', '', options.configfile)
    options.appsecret = getConfig('appsecret', '', options.configfile)
    # elastic search server settings
    options.esservers = list(getConfig('esservers', 'http://localhost:9200', options.configfile).split(','))


if __name__ == '__main__':
    parser = OptionParser()
    parser.add_option("-c", dest='configfile', default=sys.argv[0].replace('.py', '.conf'), help="configuration file to use")
    (options, args) = parser.parse_args()
    initConfig()
    initLogger(options)
    main()
