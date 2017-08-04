#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
# Copyright (c) 2014 Mozilla Corporation
#
# Contributors:
# Brandon Myers bmyers@mozilla.com

import argparse

from datetime import datetime, timedelta

import sys
import os
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'lib'))
from elasticsearch_client import ElasticsearchClient


parser = argparse.ArgumentParser(description='Create the correct indexes and aliases in elasticsearch')
parser.add_argument('esserver', help='Elasticsearch server (ex: http://elasticsearch:9200)')
args = parser.parse_args()


# This file is meant to be run from the root of the project
# even though we store this file in the mozdef container files directory
# the dockerfile moves it to the correct spot


print "Connecting to " + args.esserver
client = ElasticsearchClient(args.esserver)


current_date = datetime.now()
event_index_name = current_date.strftime("events-%Y%m%d")
previous_event_index_name = (current_date - timedelta(days=1)).strftime("events-%Y%m%d")
alert_index_name = current_date.strftime("alerts-%Y%m")


all_indices = client.get_indices()

if event_index_name not in all_indices:
    print "Creating " + event_index_name
    client.create_index(event_index_name)
client.create_alias('events', event_index_name)

if event_index_name not in previous_event_index_name:
    print "Creating " + previous_event_index_name
    client.create_index(previous_event_index_name)
client.create_alias('events-previous', previous_event_index_name)

if event_index_name not in alert_index_name:
    print "Creating " + alert_index_name
    client.create_index(alert_index_name)
client.create_alias('alerts', alert_index_name)
