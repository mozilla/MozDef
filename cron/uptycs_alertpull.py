#!/usr/bin/env python
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#

import sys
from datetime import datetime, timedelta, tzinfo

try:
    from datetime import timezone

    utc = timezone.utc
except ImportError:
    # Hi there python2 user
    class UTC(tzinfo):
        def utcoffset(self, dt):
            return timedelta(0)

        def tzname(self, dt):
            return "UTC"

        def dst(self, dt):
            return timedelta(0)

    utc = UTC()
from configlib import getConfig, OptionParser
import json
import mozdef_client as mozdef
import pickle
import datetime
import pdb
import json
import jwt
import datetime
import requests
import urllib3
import click
import os
import sys


class UptycsFilter(object):
    def __init__(self):
        utc_now = datetime.datetime.utcnow()
        self.start_time = utc_now - datetime.timedelta(days=2)
        self.end_time = utc_now
        self.sort_style = 'alertTime:desc'
        self.limit = 100
        self.offset = 0

    def filter_string(self):
        return json.dumps({
            "alertTime": {
                "between": [
                    self.start_time.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
                    self.end_time.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
                ]
            },
            "status": {"in": ["open", "assigned"]}
        }, sort_keys=False, separators=(',', ':'))


class UptycsClient(object):
    def __init__(self, path):
        self.api_json = json.load(open(path))
        self.url = 'https://' + self.api_json['domain'] + '.uptycs.io'
        self.verify_ssl = True
        self.customer_id = self.api_json['customerId']
        self.key = self.api_json['key']
        self.secret = self.api_json['secret']

    def auth_headers(self):
        headers = {}
        utcnow = datetime.datetime.utcnow()
        date = utcnow.strftime("%a, %d %b %Y %H:%M:%S GMT")
        authVar = jwt.encode({'iss': self.key}, self.secret, algorithm='HS256')
        authorization = "Bearer %s" % (authVar.decode('utf-8'))
        headers['date'] = date
        headers['Authorization'] = authorization
        return headers

    def get(self, path, params={}):
        final_url = ("%s/public/api/customers/%s%s" %
                     (self.url, self.customer_id, path))
        try:
            response = requests.get(url=final_url,
                                    headers=self.auth_headers(),
                                    verify=self.verify_ssl)
            if (response and response.status_code in
                    [requests.codes.ok, requests.codes.bad]):
                return response.json()
        except requests.exceptions.RequestException as e:
            print("ERROR: {}".format(e))

    def alerts(self, filter, sort='alertTime:desc&limit'):
        path = '/alerts?filters=' + filter.filter_string() + "&sort=" + sort
        alerts_json = self.get(path)
        return alerts_json['items']


def normalize(details):
    # Normalizes fields to conform to http://mozdef.readthedocs.io/en/latest/usage.html#mandatory-fields
    # This is mainly used for common field names to put inside the details structure
    # There might be faster ways to do this
    normalized = {}

    # for f in details:
    #     if f in ("ip", "ip_address", "client_ip"):
    #         normalized["sourceipaddress"] = details[f]
    #         continue
    #     if f == "result":
    #         if details[f].lower() == "success":
    #             normalized["success"] = True
    #         else:
    #             normalized["success"] = False
    #     normalized[f] = details[f]

    # if "user" in normalized and type(normalized["user"]) is dict:
    #     if "name" in normalized["user"]:
    #         normalized["username"] = normalized["user"]["name"]
    #     if "key" in normalized["user"]:
    #         normalized["userkey"] = normalized["user"]["key"]
    #     del (normalized["user"])

    # return normalized
    return details


def process_alerts(mozmsg, uptycs_alerts):
    for alert in uptycs_alerts:
        details = {}
        # Timestamp format: http://mozdef.readthedocs.io/en/latest/usage.html#mandatory-fields
        # Duo logs come as a UTC timestamp
        dt = datetime.utcfromtimestamp(e["timestamp"])
        mozmsg.timestamp = dt.replace(tzinfo=utc).isoformat()

        # TODO: Fix this so hostName is properly set
        mozmsg.log["hostname"] = alert["host"]
        for item in alert:
            details[item] = alert[item]

        localdetails = normalize(details)
        mozmsg.details = localdetails
        mozmsg.summary = (
            alert["eventtype"] + " " + alert["result"] + " for " + alert["username"]
        )
        mozmsg.send()


def main():
    mozmsg = mozdef.MozDefEvent(options.MOZDEF_URL)
    mozmsg.tags = ["uptycs"]
    mozmsg.set_category("uptycs")
    mozmsg.source = "UptycsAPI"
    if options.DEBUG:
        mozmsg.debug = options.DEBUG
        mozmsg.set_send_to_syslog(True, only_syslog=True)

    client = UptycsClient(options.UPTYCS_API_JSON_FILE)

    # Adjust the filter as needed to set proper search window
    filter = UptycsFilter()
    utc_now = datetime.datetime.utcnow()

    # If an existing state file exists, set our start window to last run
    if os.path.exists(options.statepath):
        state = pickle.load(open(options.statepath, 'rb'))
        filter.start_time = state["last_run"]
        last_alert_ids = state["last_alert_ids"]
    else:
        last_alert_ids = []
        filter.start_time = utc_now - datetime.timedelta(days=30)

    filter.end_time = utc_now

    # Query alerts that match the filter
    alerts = client.alerts(filter)

    # Process all these alerts in MozDef
    process_alerts(mozmsg, alerts)

    state = {
        "last_run": filter.end_time,
        "last_alert_ids": alert_ids,
    }
    pickle.dump(state, open("poc.state", "wb"))


def initConfig():
    options.UPTYCS_API_JSON_FILE = getConfig("UPTYCS_API_JSON_FILE", "", options.configfile)
    options.MOZDEF_URL = getConfig("MOZDEF_URL", "", options.configfile)
    options.DEBUG = getConfig("DEBUG", True, options.configfile)
    options.statepath = getConfig("statepath", "", options.configfile)


if __name__ == "__main__":
    parser = OptionParser()
    defaultconfigfile = sys.argv[0].replace(".py", ".conf")
    parser.add_option(
        "-c",
        dest="configfile",
        default=defaultconfigfile,
        help="configuration file to use",
    )
    (options, args) = parser.parse_args()
    initConfig()
    main()
