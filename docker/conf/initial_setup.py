#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
# Copyright (c) 2014 Mozilla Corporation

import argparse

from datetime import datetime, timedelta
from time import sleep
from configlib import getConfig
import json

from elasticsearch.exceptions import ConnectionError

import sys
import os
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../lib'))
from elasticsearch_client import ElasticsearchClient


parser = argparse.ArgumentParser(description='Create the correct indexes and aliases in elasticsearch')
parser.add_argument('esserver', help='Elasticsearch server (ex: http://elasticsearch:9200)')
parser.add_argument('default_mapping_file', help='The relative path to default mapping json file (ex: cron/defaultTemplateMapping.json)')
parser.add_argument('backup_conf_file', help='The relative path to backup.conf file (ex: cron/backup.conf)')
args = parser.parse_args()


print "Connecting to " + args.esserver
client = ElasticsearchClient(args.esserver)


current_date = datetime.now()
event_index_name = current_date.strftime("events-%Y%m%d")
previous_event_index_name = (current_date - timedelta(days=1)).strftime("events-%Y%m%d")
weekly_index_alias = 'events-weekly'
alert_index_name = current_date.strftime("alerts-%Y%m")

index_settings_str = ''
with open(args.default_mapping_file) as data_file:
    index_settings_str = data_file.read()

index_settings = json.loads(index_settings_str)

all_indices = []
total_num_tries = 15
for attempt in range(total_num_tries):
    try:
        all_indices = client.get_indices()
    except ConnectionError:
        print 'Unable to connect to Elasticsearch...retrying'
        sleep(5)
    else:
        break
else:
    print 'Cannot connect to Elasticsearch after ' + str(total_num_tries) + ' tries, exiting script.'
    exit(1)

refresh_interval = getConfig('refresh_interval', '1s', args.backup_conf_file)
number_of_shards = getConfig('number_of_shards', '1', args.backup_conf_file)
number_of_replicas = getConfig('number_of_replicas', '1', args.backup_conf_file)
slowlog_threshold_query_warn = getConfig('slowlog_threshold_query_warn', '5s', args.backup_conf_file)
slowlog_threshold_fetch_warn = getConfig('slowlog_threshold_fetch_warn', '5s', args.backup_conf_file)
mapping_total_fields_limit = getConfig('mapping_total_fields_limit', '1000', args.backup_conf_file)

index_settings['settings'] = {
    "index": {
        "refresh_interval": refresh_interval,
        "number_of_shards": number_of_shards,
        "number_of_replicas": number_of_replicas,
        "search.slowlog.threshold.query.warn": slowlog_threshold_query_warn,
        "search.slowlog.threshold.fetch.warn": slowlog_threshold_fetch_warn,
        "mapping.total_fields.limit": mapping_total_fields_limit
    }
}

if event_index_name not in all_indices:
    print "Creating " + event_index_name
    client.create_index(event_index_name, index_config=index_settings)
client.create_alias('events', event_index_name)

if previous_event_index_name not in all_indices:
    print "Creating " + previous_event_index_name
    client.create_index(previous_event_index_name, index_config=index_settings)
client.create_alias('events-previous', previous_event_index_name)

if alert_index_name not in all_indices:
    print "Creating " + alert_index_name
    client.create_index(alert_index_name)
client.create_alias('alerts', alert_index_name)

if weekly_index_alias not in all_indices:
    print "Creating " + weekly_index_alias
    client.create_alias_multiple_indices(weekly_index_alias, [event_index_name, previous_event_index_name])
