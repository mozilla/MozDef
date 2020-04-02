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

GEOMODEL_EVT1 = {
    "receivedtimestamp": "2020-04-02T13:10:02.529570+00:00",
    "mozdefhostname": "mozdef4.private.mdc1.mozilla.com",
    "details": {
        "clientid": "383wZyKOqULjvIJnA4Njz04lztkmxKjf",
        "clientname": "auth0proxy.stage.mozaws.net",
        "connection": "Mozilla-LDAP",
        "description": "None",
        "eventname": "Success Login",
        "messageid": "5e85e3f15ae00a0d5de080d3",
        "raw": "{'_id': '5e85e3f15ae00a0d5de080d3', 'date': '2020-04-02T13:09:05.828Z', 'type': 's', 'description': 'None', 'connection': 'Mozilla-LDAP', 'connection_id': 'con_dc6SPKopkKT33i70', 'client_id': '383wZyKOqULjvIJnA4Njz04lztkmxKjf', 'client_name': 'auth0proxy.stage.mozaws.net', 'ip': '92.86.91.173', 'client_ip': 'None', 'user_agent': 'Firefox 74.0.0 / Windows 10.0.0', 'details': {'prompts': [{'name': 'authenticate', 'initiatedAt': '1585832945140', 'completedAt': '1585832945414', 'connection': 'Mozilla-LDAP', 'connection_id': 'con_dc6SPKopkKT33i70', 'strategy': 'ad', 'identity': 'Mozilla-LDAP|mheres', 'stats': {'loginsCount': '457'}, 'elapsedTime': '274'}, {'name': 'login', 'flow': 'login', 'initiatedAt': '1585832943359', 'completedAt': '1585832945417', 'timers': {'rules': '400'}, 'user_id': 'ad|Mozilla-LDAP|mheres', 'user_name': 'mheres@mozilla.com', 'elapsedTime': '2058'}], 'initiatedAt': '1585832943358', 'completedAt': '1585832945827', 'elapsedTime': '2469', 'session_id': 'H40UB6waQ_kjqkcZSO1ITocASMLVrM5c', 'device_id': 'v0:0acc2680-f1a5-11e9-b0be-418e1360eac5', 'stats': {'loginsCount': '457'}}, 'hostname': 'auth.mozilla.auth0.com', 'user_id': 'ad|Mozilla-LDAP|mheres', 'user_name': 'mheres@mozilla.com', 'strategy': 'ad', 'strategy_type': 'enterprise', 'isMobile': 'False'}",
        "sourceipaddress": "92.86.91.173",
        "success": True,
        "useragent": "Firefox 74.0.0 / Windows 10.0.0",
        "userid": "ad|Mozilla-LDAP|mheres",
        "username": "mheres@mozilla.com",
        "sourceipv4address": "92.86.91.173",
        "sourceipgeolocation": {
            "city": "Dumbravita",
            "continent": "EU",
            "country_code": "RO",
            "country_name": "Romania",
            "dma_code": None,
            "latitude": 47.6,
            "longitude": 23.65,
            "metro_code": "Dumbravita, MM",
            "postal_code": "437145",
            "region_code": "MM",
            "time_zone": "Europe/Bucharest",
        },
        "sourceipgeopoint": "47.6,23.65",
    },
    "category": "authentication",
    "hostname": "https://auth.mozilla.auth0.com/api/v2/logs",
    "processid": "2192",
    "processname": "/opt/mozdef/envs/mozdef/cron/auth02mozdef.py",
    "severity": "INFO",
    "summary": "Success Login mheres@mozilla.com",
    "tags": ["auth0"],
    "utctimestamp": "2020-04-02T13:09:05.828000+00:00",
    "timestamp": "2020-04-02T13:09:05.828000+00:00",
    "type": "event",
    "plugins": ["ipFixup", "geoip"],
    "source": "UNKNOWN",
}

GEOMODEL_EVT2 = {
    "receivedtimestamp": "2020-04-02T13:10:02.529570+00:00",
    "mozdefhostname": "mozdef4.private.mdc1.mozilla.com",
    "details": {
        "clientid": "383wZyKOqULjvIJnA4Njz04lztkmxKjf",
        "clientname": "auth0proxy.stage.mozaws.net",
        "connection": "Mozilla-LDAP",
        "description": "None",
        "eventname": "Success Login",
        "messageid": "5e85e3f15ae00a0d5de080d3",
        "raw": "{'_id': '5e85e3f15ae00a0d5de080d3', 'date': '2020-04-02T13:09:05.828Z', 'type': 's', 'description': 'None', 'connection': 'Mozilla-LDAP', 'connection_id': 'con_dc6SPKopkKT33i70', 'client_id': '383wZyKOqULjvIJnA4Njz04lztkmxKjf', 'client_name': 'auth0proxy.stage.mozaws.net', 'ip': '92.86.91.173', 'client_ip': 'None', 'user_agent': 'Firefox 74.0.0 / Windows 10.0.0', 'details': {'prompts': [{'name': 'authenticate', 'initiatedAt': '1585832945140', 'completedAt': '1585832945414', 'connection': 'Mozilla-LDAP', 'connection_id': 'con_dc6SPKopkKT33i70', 'strategy': 'ad', 'identity': 'Mozilla-LDAP|mheres', 'stats': {'loginsCount': '457'}, 'elapsedTime': '274'}, {'name': 'login', 'flow': 'login', 'initiatedAt': '1585832943359', 'completedAt': '1585832945417', 'timers': {'rules': '400'}, 'user_id': 'ad|Mozilla-LDAP|mheres', 'user_name': 'mheres@mozilla.com', 'elapsedTime': '2058'}], 'initiatedAt': '1585832943358', 'completedAt': '1585832945827', 'elapsedTime': '2469', 'session_id': 'H40UB6waQ_kjqkcZSO1ITocASMLVrM5c', 'device_id': 'v0:0acc2680-f1a5-11e9-b0be-418e1360eac5', 'stats': {'loginsCount': '457'}}, 'hostname': 'auth.mozilla.auth0.com', 'user_id': 'ad|Mozilla-LDAP|mheres', 'user_name': 'mheres@mozilla.com', 'strategy': 'ad', 'strategy_type': 'enterprise', 'isMobile': 'False'}",
        "sourceipaddress": "178.62.244.168",
        "success": True,
        "useragent": "Firefox 74.0.0 / Windows 10.0.0",
        "userid": "ad|Mozilla-LDAP|mheres",
        "username": "mheres@mozilla.com",
        "sourceipv4address": "178.62.244.168",
        "sourceipgeolocation": {
            "city": "Dallas",
            "continent": "NA",
            "country_code": "US",
            "country_name": "USA",
            "dma_code": None,
            "latitude": 32.8137,
            "longitude": -96.8704,
            "metro_code": "Dumbravita, MM",
            "postal_code": "437145",
            "region_code": "DA",
            "time_zone": "America/Dallas",
        },
        "sourceipgeopoint": "32.8137,-96.8704",
    },
    "category": "authentication",
    "hostname": "https://auth.mozilla.auth0.com/api/v2/logs",
    "processid": "2192",
    "processname": "/opt/mozdef/envs/mozdef/cron/auth02mozdef.py",
    "severity": "INFO",
    "summary": "Success Login mheres@mozilla.com",
    "tags": ["auth0"],
    "utctimestamp": "2020-04-02T13:09:05.828000+00:00",
    "timestamp": "2020-04-02T13:09:05.828000+00:00",
    "type": "event",
    "plugins": ["ipFixup", "geoip"],
    "source": "UNKNOWN",
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

    GEOMODEL_EVT1,
    GEOMODEL_EVT2,
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
