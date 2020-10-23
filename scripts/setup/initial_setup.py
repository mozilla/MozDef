#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# Copyright (c) 2014 Mozilla Corporation

import argparse

from datetime import datetime, timedelta
from pathlib import Path
from time import sleep
from configlib import getConfig
import json
import os
import sys

from elasticsearch.exceptions import ConnectionError
import requests

from mozdef_util.elasticsearch_client import ElasticsearchClient

cron_dir_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../cron')

parser = argparse.ArgumentParser(description='Create the correct indexes and aliases in elasticsearch')
parser.add_argument('esserver', help='Elasticsearch server (ex: http://elasticsearch:9200)')

default_file = os.path.realpath(cron_dir_path + '/defaultMappingTemplate.json')
parser.add_argument(
    'default_mapping_file',
    help='The relative path to default mapping json file (default: {0})'.format(default_file),
    default=default_file,
    nargs='?'
)

default_file = os.path.realpath(cron_dir_path + '/mozdefStateDefaultMappingTemplate.json')
parser.add_argument(
    'state_mapping_file',
    help='The relative path to state mapping json file (default: {0})'.format(default_file),
    default=default_file,
    nargs='?'
)

default_file = os.path.realpath(cron_dir_path + '/rotateIndexes.conf')
parser.add_argument(
    'backup_conf_file',
    help='The relative path to rotateIndexes.conf file (default: {0})'.format(default_file),
    default=default_file,
    nargs='?'
)

parser.add_argument('kibana_url', help='The URL of the kibana endpoint (ex: http://kibana:5601)')
args = parser.parse_args()


esserver = os.environ.get('OPTIONS_ESSERVERS')
if esserver is None:
    esserver = args.esserver
esserver = esserver.strip('/')
print("Connecting to " + esserver)
client = ElasticsearchClient(esserver)

kibana_url = os.environ.get('OPTIONS_KIBANAURL', args.kibana_url)

current_date = datetime.now()
event_index_name = current_date.strftime("events-%Y%m%d")
previous_event_index_name = (current_date - timedelta(days=1)).strftime("events-%Y%m%d")
weekly_index_alias = 'events-weekly'
alert_index_name = current_date.strftime("alerts-%Y%m")

kibana_index_name = '.kibana_1'
state_index_name = 'mozdefstate'

index_settings_str = ''
with open(args.default_mapping_file) as data_file:
    index_settings_str = data_file.read()

index_settings = json.loads(index_settings_str)

state_index_settings_str = ''
with open(args.state_mapping_file) as data_file:
    state_index_settings_str = data_file.read()

state_index_settings = json.loads(state_index_settings_str)


all_indices = []
total_num_tries = 15
for attempt in range(total_num_tries):
    try:
        all_indices = client.get_indices()
    except ConnectionError:
        print('Unable to connect to Elasticsearch...retrying')
        sleep(5)
    else:
        break
else:
    print('Cannot connect to Elasticsearch after ' + str(total_num_tries) + ' tries, exiting script.')
    exit(1)

refresh_interval = getConfig('refresh_interval', '1s', args.backup_conf_file)
number_of_shards = getConfig('number_of_shards', '1', args.backup_conf_file)
number_of_replicas = getConfig('number_of_replicas', '1', args.backup_conf_file)
slowlog_threshold_query_warn = getConfig('slowlog_threshold_query_warn', '5s', args.backup_conf_file)
slowlog_threshold_fetch_warn = getConfig('slowlog_threshold_fetch_warn', '5s', args.backup_conf_file)
mapping_total_fields_limit = getConfig('mapping_total_fields_limit', '1000', args.backup_conf_file)

index_options = {
    "index": {
        "refresh_interval": refresh_interval,
        "number_of_shards": number_of_shards,
        "number_of_replicas": number_of_replicas,
        "search.slowlog.threshold.query.warn": slowlog_threshold_query_warn,
        "search.slowlog.threshold.fetch.warn": slowlog_threshold_fetch_warn,
        "mapping.total_fields.limit": mapping_total_fields_limit
    }
}
index_settings['settings'] = index_options
state_index_settings['settings'] = index_options

# Create initial indices
if event_index_name not in all_indices:
    print("Creating " + event_index_name)
    client.create_index(event_index_name, index_config=index_settings)
client.create_alias('events', event_index_name)

if previous_event_index_name not in all_indices:
    print("Creating " + previous_event_index_name)
    client.create_index(previous_event_index_name, index_config=index_settings)
client.create_alias('events-previous', previous_event_index_name)

if alert_index_name not in all_indices:
    print("Creating " + alert_index_name)
    client.create_index(alert_index_name, index_config=index_settings)
client.create_alias('alerts', alert_index_name)

if weekly_index_alias not in all_indices:
    print("Creating " + weekly_index_alias)
    client.create_alias_multiple_indices(weekly_index_alias, [event_index_name, previous_event_index_name])

if state_index_name not in all_indices:
    print("Creating " + state_index_name)
    client.create_index(state_index_name, index_config=state_index_settings)

# Wait for kibana service to get ready
total_num_tries = 20
for attempt in range(total_num_tries):
    try:
        if requests.get(kibana_url, allow_redirects=True):
            break
    except Exception:
        pass
    print('Unable to connect to Kibana ({0})...retrying'.format(kibana_url))
    sleep(5)
else:
    print('Cannot connect to Kibana after ' + str(total_num_tries) + ' tries, exiting script.')
    exit(1)

# Check if index-patterns already exist
if kibana_index_name in client.get_indices():
    existing_patterns_url = kibana_url + "/api/saved_objects/_find?type=index-pattern&search_fields=title&search=*"
    resp = requests.get(url=existing_patterns_url)
    existing_patterns = json.loads(resp.text)
    if len(existing_patterns['saved_objects']) > 0:
        print("Index patterns already exist, exiting script early")
        sys.exit(0)

kibana_headers = {'content-type': 'application/json', 'kbn-xsrf': 'true'}

# Create index-patterns
current_dir_path = Path(__file__).resolve().parent
for file in current_dir_path.joinpath("index_mappings").glob("*.json"):
    with open(file, "r") as f:
        mapping_data = json.load(f)
        index_name = mapping_data['attributes']['title']
        # Transform data["attributes"]["field"] to a string
        mapping_data["attributes"]["fields"] = json.dumps(mapping_data["attributes"]["fields"])
        print("Creating {0} index mapping".format(index_name))
        mapping_url = kibana_url + "/api/saved_objects/index-pattern/" + index_name
        resp = requests.post(url=mapping_url, data=json.dumps(mapping_data), headers=kibana_headers)
        if not resp.ok:
            print("Unable to create index mapping: " + resp.text)

# Set default index mapping to events-*
data = {
    "value": "events-*"
}
print("Creating default index pattern for events-*")
resp = requests.post(url=kibana_url + "/api/kibana/settings/defaultIndex", data=json.dumps(data), headers=kibana_headers)
if not resp.ok:
    print("Failed to set default index: {} {}".format(resp.status_code, resp.content))

# Check if dashboards already exist
if kibana_index_name in client.get_indices():
    existing_patterns_url = kibana_url + "/api/saved_objects/_find?type=dashboard&search_fields=title&search=*"
    resp = requests.get(url=existing_patterns_url)
    existing_patterns = json.loads(resp.text)
    if len(existing_patterns['saved_objects']) > 0:
        print("Dashboards already exist, exiting script early")
        sys.exit(0)

# Create visualizations/dashboards
dashboards_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'example_resources')
listing = os.listdir(dashboards_path)
for infile in listing:
    json_file_path = os.path.join(dashboards_path, infile)
    with open(json_file_path) as json_data:
        mapping_data = json.load(json_data)
        mapping_type = mapping_data['type']
        print("Creating {0} {1}".format(
            mapping_data[mapping_type]['title'],
            mapping_type
        ))
        post_data = {
            "attributes": mapping_data[mapping_type]
        }
        # We use the filename as the id of the resource
        resource_name = infile.replace('.json', '')
        kibana_type_url = kibana_url + "/api/saved_objects/" + mapping_type + "/" + resource_name
        requests.post(url=kibana_type_url, data=json.dumps(post_data), headers=kibana_headers)
