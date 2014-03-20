#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
# Copyright (c) 2014 Mozilla Corporation
# Contributors:
# gdestuynder@mozilla.com
# mpurzynski@mozilla.com
# jbryner@mozilla.com

# Message sample
# {
#    "category": "authentication",
#    "details": {
#        "uid": 0,
#        "username": "kang"
#    },
#    "hostname": "blah.private.scl3.mozilla.com",
#    "processid": 14619,
#    "processname": "./mozdef.py",
#    "severity": "CRITICAL",
#    "summary": "new test msg",
#    "tags": [
#        "bro",
#        "auth"
#    ],
#    "timestamp": "2014-03-18T23:20:31.013344+00:00"
# }

# Module usage:
# import mozdef
# msg = mozdef.MozDefMsg('https://127.0.0.1:8443/events')
# msg.verify_certificate = False # not recommended, security issue.
# msg.verify_certificate = True # uses default certs from /etc/ssl/certs
# msg.verify_certificate = '/etc/path/to/custom/cert'
# msg.send('hello there')
# msg.send('hello again', details={'uid': 0})
# another_msg = mozdef.MozDefMsg('https://127.0.0.1:8443/events', tags=['bro'])
# another_msg.send('knock knock')
# another_msg.log['some-internal-attribute']
# another_msg.send('who's there?')
# etc.
#
# note: it is recommended to fill-in details={}, category='' and severity='' even thus those are optional
# note: if you get a certificate failure, you can msg.verify_certificate = False - however this is not recommended,
# and introduces a security issue. Use it for testing only.

# TODO:
# - Could report to syslog when fire_and_forget_mode is True and we fail
# - Might be nicer to store the log msg as an object rather than a dict (such as MozDefLog.timestamp, MozDefLog.tags, etc.)
# - Might want to limit category to well-known default categories instead of a string (such as "authentication", "daemon", etc.)
# - Might want to limit severities to well-known default severities instead of a string (such as INFO, DEBUG, WARNING, CRITICAL, etc.)
# - Might want to add documentation how to add your own CA certificate for this program to use

import os
import sys
import copy
from datetime import datetime
import pytz
import json
import socket
from requests_futures.sessions import FuturesSession


class MozDefError(Exception):
    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return repr(self.msg)

class MozDefMsg():
    httpsession = FuturesSession(max_workers=20)
#Turns off needless and repetitive .netrc check for creds
    httpsession.trust_env = False
    debug = False
    verify_certificate = True
#Never fail (ie no unexcepted exceptions sent to user, such as server/network not responding)
    fire_and_forget_mode = True
    log = {}
    log['timestamp']   = pytz.timezone('UTC').localize(datetime.now()).isoformat()
    log['hostname']    = socket.getfqdn()
    log['processid']   = os.getpid()
    log['processname'] = sys.argv[0]
    log['severity']    = 'INFO'
    log['summary']     = None
    log['category']    = 'event'
    log['tags']        = list()
    log['details']     = dict()

    def __init__(self, mozdef_hostname, summary=None, category='event', severity='INFO', tags=[], details={}):
        self.summary = summary
        self.category = category
        self.severity = severity
        self.tags = tags
        self.details = details
        self.mozdef_hostname = mozdef_hostname

    def send(self, summary=None, category=None, severity=None, tags=None, details=None):
        log_msg = copy.copy(self.log)

        if summary == None: log_msg['summary'] = self.summary
        else:               log_msg['summary'] = summary

        if category == None: log_msg['category'] = self.category
        else:                log_msg['category'] = category

        if severity == None: log_msg['severity'] = self.severity
        else:                log_msg['severity'] = severity

        if tags == None: log_msg['tags'] = self.tags
        else:            log_msg['tags'] = tags

        if details == None: log_msg['details'] = self.details
        else:               log_msg['details'] = details

        if type(log_msg['details']) != dict:
            raise MozDefError('details must be a dict')
        elif type(log_msg['tags']) != list:
            raise MozDefError('tags must be a list')
        elif summary == None:
            raise MozDefError('Summary is a required field')

        if self.debug:
           print(json.dumps(log_msg, sort_keys=True, indent=4))
           return

        try:
            r = self.httpsession.post(self.mozdef_hostname, json.dumps(log_msg, sort_keys=True, indent=4), verify=self.verify_certificate, background_callback=self.httpsession_cb)
        except Exception as e:
            if not self.fire_and_forget_mode:
                raise e

    def httpsession_cb(self, session, response):
        if response.result().status_code != 200:
            if not self.fire_and_forget_mode:
                raise MozDefError("HTTP POST failed with code %r" % response.result().status_code)

if __name__ == "__main__":
    print("Testing the MozDef logging module (no msg sent over the network)")
    print("Simple msg:")
    msg = MozDefMsg('https://127.0.0.1/events')
    msg.debug = True
    msg.send('test msg')

    print("Complex msg:")
    msg.send('new test msg', 'authentication', 'CRITICAL', ['bro', 'auth'], {'uid': 0, 'username': 'kang'})

    print("Modifying timestamp attribute:")
    msg.log['timestamp'] = pytz.timezone('Europe/Paris').localize(datetime.now()).isoformat()
    msg.send('another test msg')
