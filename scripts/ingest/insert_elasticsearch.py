#!/usr/bin/env python

from datetime import datetime
import optparse

import random
import time

from mozdef_util.utilities.toUTC import toUTC
from mozdef_util.elasticsearch_client import ElasticsearchClient


# A utility function to generate random ips to fill into event
def random_ip():
    return ".".join([random.randint(1, 255) for _ in range(4)])


parser = optparse.OptionParser()
parser.add_option(
    "--elasticsearch_host",
    help="Elasticsearch host (default: http://localhost:9200)",
    default="http://localhost:9200",
)
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
        "receivedtimestamp": "2020-02-03T09:15:31.193369+00:00",
        "mozdefhostname": "mozdef4.private.mdc1.mozilla.com",
        "details": {
            "id": "1160915410711908357",
            "source_ip": "34.209.253.181",
            "program": "sshd",
            "message": "Accepted publickey for emrose from 10.49.48.100 port 47666 ssh2",
            "received_at": "2020-02-03T09:10:25Z",
            "generated_at": "2020-02-03T09:10:25Z",
            "display_received_at": "Feb 03 09:10:25",
            "source_id": 4460489962,
            "source_name": "mergeday1.srv.releng.usw2.mozilla.com",
            "hostname": "mergeday1.srv.releng.usw2.mozilla.com",
            "severity": "Info",
            "facility": "Auth",
            "sourceipaddress": "10.49.48.100",
            "sourceipv4address": "10.49.48.100",
        },
        "tags": ["papertrail", "releng"],
        "utctimestamp": "2020-02-03T09:10:25+00:00",
        "timestamp": "2020-02-03T09:10:25+00:00",
        "hostname": "mergeday1.srv.releng.usw2.mozilla.com",
        "summary": "Accepted publickey for emrose from 10.49.48.100 port 47666 ssh2",
        "severity": "INFO",
        "category": "syslog",
        "type": "event",
        "plugins": ["parse_sshd", "parse_su", "sshdFindIP", "ipFixup", "geoip"],
        "processid": "UNKNOWN",
        "processname": "UNKNOWN",
        "source": "UNKNOWN",
    },
    {
        "receivedtimestamp": "2020-02-05T02:52:34.609317+00:00",
        "mozdefhostname": "mozdef3.private.mdc1.mozilla.com",
        "details": {
            "program": "sshd",
            "eventsourceipaddress": "10.48.75.114",
            "username": "emrose",
        },
        "tags": [".source.moz_net"],
        "source": "authpriv",
        "processname": "sshd",
        "severity": "INFO",
        "processid": "30171",
        "summary": "pam_unix(sshd:session): session opened for user emrose by (uid=0)",
        "hostname": "mozdefqa2.private.mdc1.mozilla.com",
        "facility": "authpriv",
        "utctimestamp": "2020-02-05T02:52:34+00:00",
        "timestamp": "2020-02-05T02:52:34+00:00",
        "category": "syslog",
        "type": "event",
        "plugins": ["parse_sshd", "parse_su", "sshdFindIP"],
    },
]

es_client = ElasticsearchClient(options.elasticsearch_host)

for event in events:
    timestamp = toUTC(datetime.now()).isoformat()
    event["utctimestamp"] = timestamp
    event["timestamp"] = timestamp
    event["receivedtimestamp"] = timestamp
    es_client.save_event(body=event)
    print("Wrote event to elasticsearch")
    time.sleep(0.2)
