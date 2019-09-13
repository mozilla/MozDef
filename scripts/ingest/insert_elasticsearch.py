#!/usr/bin/env python

from datetime import datetime
import optparse

import random
import socket
import time

from mozdef_util.utilities.toUTC import toUTC
from mozdef_util.elasticsearch_client import ElasticsearchClient


# A utility function to generate random ips to fill into event
def random_ip():
    return str(random.randint(1, 255)) + "." + str(random.randint(1, 255)) + \
        "." + str(random.randint(1, 255)) + "." + str(random.randint(1, 255))


parser = optparse.OptionParser()
parser.add_option('--elasticsearch_host', help='Elasticsearch host (default: http://localhost:9200)', default='http://localhost:9200')
options, arguments = parser.parse_args()


# Placeholders for variables from kibana -> python
# NO NEED TO MODIFY
true = True
false = False
null = None

# Fill in with events you want to write to elasticsearch
# NEED TO MODIFY
events = [
    {
        "category": "testcategory",
        "details": {
            "program": "sshd",
            "type": "Success Login",
            "username": "ttesterson",
            "sourceipaddress": random_ip(),
        },
        "hostname": "i-99999999",
        "mozdefhostname": socket.gethostname(),
        "processid": "1337",
        "processname": "auth0_cron",
        "severity": "INFO",
        "source": "auth0",
        "summary": "login invalid ldap_count_entries failed",
        "tags": ["auth0"],
    }
]

es_client = ElasticsearchClient(options.elasticsearch_host)

for event in events:
    timestamp = toUTC(datetime.now()).isoformat()
    event['utctimestamp'] = timestamp
    event['timestamp'] = timestamp
    event['receivedtimestamp'] = timestamp
    es_client.save_event(body=event)
    print("Wrote event to elasticsearch")
    time.sleep(0.2)
