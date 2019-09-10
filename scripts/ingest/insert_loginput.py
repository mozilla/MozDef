#!/usr/bin/env python

import time
import optparse

import mozdef_client as mozdef

parser = optparse.OptionParser()
parser.add_option('--loginput_host', help='MozDef Loginput host (default: http://127.0.0.1:8080)', default='http://127.0.0.1:8080')
parser.add_option('--num_times', help='Number of times event is sent to loginput (default: 20)', default=20)
options, arguments = parser.parse_args()

# Fill in with events you want to write
events = [
    {
        "category": "testcategory",
        "details": {
            "program": "sshd",
            "type": "Success Login",
            "username": "ttesterson",
            "sourceipaddress": '1.2.3.4',
        },
        "processname": "auth0_cron",
        "severity": "INFO",
        "source": "auth0",
        "summary": "login invalid ldap_count_entries failed",
        "tags": ["auth0"],
    }
]

for num in range(0, options.num_times):
    for event in events:
        mozmsg = mozdef.MozDefEvent(options.loginput_host + "/events/")
        for key, value in event.items():
            setattr(mozmsg, key, value)
        mozmsg.send()
        print("Wrote event to loginput")
        time.sleep(0.2)
