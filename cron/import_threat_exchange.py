#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
# Copyright (c) 2017 Mozilla Corporation
#
# Contributors:
# Brandon Myers bmyers@mozilla.com

import os
import sys
from configlib import getConfig, OptionParser
from datetime import datetime
from datetime import timedelta

from pytx.access_token import access_token
from pytx import ThreatIndicator
from pytx import Malware

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../lib'))
from utilities.logger import logger, initLogger
from utilities.toUTC import toUTC
from elasticsearch_client import ElasticsearchClient

from state import State


def pull_malware_hashes(since_date, until_date):
    query_params = {
        'since': str(since_date),
        'until': str(until_date),
        'dict_generator': True,
    }
    logger.info('Querying threat exchange with params {}'.format(query_params))
    results = Malware.objects(**query_params)
    malware_data = []
    for result in results:
        created_date = toUTC(datetime.now()).isoformat()
        es_doc = {
            'created_on': created_date,
            'details': result
        }
        malware_data.append(es_doc)
    return malware_data


def pull_ip_addresses(since_date, until_date):
    query_params = {
        'type_': 'IP_ADDRESS',
        'since': str(since_date),
        'until': str(until_date),
        'dict_generator': True,
    }
    logger.info('Querying threat exchange with params {}'.format(query_params))
    results = ThreatIndicator.objects(**query_params)
    ip_address_data = []
    for result in results:
        created_date = toUTC(datetime.now()).isoformat()
        es_doc = {
            'created_on': created_date,
            'details': result
        }
        ip_address_data.append(es_doc)
    return ip_address_data


def main():
    logger.info('Connecting to Elasticsearch')
    client = ElasticsearchClient(options.esservers)
    logger.info('Connecting to threat exchange')
    access_token(options.appid, options.appsecret)
    state = State(options.state_file_name)
    current_timestamp = toUTC(datetime.now()).isoformat()
    # We're setting a default for the past 2 days of data
    # if there isnt a state file
    since_date_obj = toUTC(datetime.now()) - timedelta(days=2)
    since_date = since_date_obj.isoformat()
    if 'lastrun' in state.data.keys():
        since_date = state.data['lastrun']

    malware_hashes_docs = pull_malware_hashes(since_date=since_date, until_date=current_timestamp)
    logger.info('Saving {} hashes to ES'.format(len(malware_hashes_docs)))
    for malware_hash_doc in malware_hashes_docs:
        client.save_object(index='threat-exchange', doc_type='malware_hashes', body=malware_hash_doc)

    ip_addresses_docs = pull_ip_addresses(since_date=since_date, until_date=current_timestamp)
    logger.info('Saving {} ip addresses to ES'.format(len(ip_addresses_docs)))
    for ip_addresses_doc in ip_addresses_docs:
        client.save_object(index='threat-exchange', doc_type='ip_address', body=ip_addresses_doc)

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
