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

SSH_ACCESS_EVENT = {
    "receivedtimestamp": "2020-04-15T22:01:33.799290+00:00",
    "mozdefhostname": "mozdef1.private.mdc1.mozilla.com",
    "details": {
        "program": "sshd",
        "eventsourceipaddress": "10.48.75.211",
        "username": "emrose",
    },
    "tags": [".source.moz_net"],
    "source": "authpriv",
    "processname": "sshd",
    "severity": "INFO",
    "processid": "31365",
    "summary": "pam_unix(sshd:session): session opened for user emrose by (uid=0)",
    "hostname": "mozdefalert.private.mdc1.mozilla.com",
    "facility": "authpriv",
    "utctimestamp": "2020-04-15T22:01:33+00:00",
    "timestamp": "2020-04-15T22:01:33+00:00",
    "category": "syslog",
    "type": "event",
    "plugins": ["parse_sshd", "parse_su", "sshdFindIP"],
}

# Fill in with events you want to write to elasticsearch
# NEED TO MODIFY
events = [
#    {
#        "category": "testcategory",
#        "details": {
#            "program": "sshd",
#            "type": "Success Login",
#            "username": "ttesterson",
#            "sourceipaddress": random_ip(),
#        },
#        "hostname": "i-99999999",
#        "mozdefhostname": socket.gethostname(),
#        "processid": "1337",
#        "processname": "auth0_cron",
#        "severity": "INFO",
#        "source": "auth0",
#        "summary": "login invalid ldap_count_entries failed",
#        "tags": ["auth0"],
#    }
    SSH_ACCESS_EVENT,
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
