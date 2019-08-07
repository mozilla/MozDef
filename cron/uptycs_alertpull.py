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
# TODO: to write/vendor this client
# import uptycs_client
import pickle


def normalize(details):
    # Normalizes fields to conform to http://mozdef.readthedocs.io/en/latest/usage.html#mandatory-fields
    # This is mainly used for common field names to put inside the details structure
    # There might be faster ways to do this
    normalized = {}

    for f in details:
        if f in ("ip", "ip_address", "client_ip"):
            normalized["sourceipaddress"] = details[f]
            continue
        if f == "result":
            if details[f].lower() == "success":
                normalized["success"] = True
            else:
                normalized["success"] = False
        normalized[f] = details[f]

    if "user" in normalized and type(normalized["user"]) is dict:
        if "name" in normalized["user"]:
            normalized["username"] = normalized["user"]["name"]
        if "key" in normalized["user"]:
            normalized["userkey"] = normalized["user"]["key"]
        del (normalized["user"])

    return normalized


def process_alerts(mozmsg, uptycs_alerts):
    """
    Data format of duo_events in api_version == 2 (str):
    duo_events.metadata = {u'total_objects': 49198, u'next_offset': [u'1547244648000', u'4da7180c-b1e5-47b4-9f4d-ee10dc3b5ac8']}
    duo_events.authlogs = [{...}, {...}, ...]
    authlogs entry = {u'access_device': {u'ip': u'a.b.c.d', u'location': {u'city': None, u'state': u'Anhui', u'country':
    u'China'}}, u'event_type': u'authentication', u'timestamp': 1547244800, u'factor': u'not_available', u'reason':
    u'deny_unenrolled_user', u'txid': u'68b33dd3-d341-46c6-a985-0640592fb7b0', u'application': {u'name': u'Integration
    Name Here', u'key': u'SOME KEY HERE'}, u'host': u'api-blah.duosecurity.com', u'result': u'denied', u'eventtype': u'authentication', u'auth_device': {u'ip': None, u'location': {u'city': None, u'state': None, u'country': None}, u'name': None}, u'user': {u'name': u'root', u'key': None}}
    """
    # There are some key fields that we use as MozDef fields, those are set to "noconsume"
    # After processing these fields, we just pour everything into the "details" fields of Mozdef, except for the
    # noconsume fields.

    if etype == "administration":
        noconsume = ["timestamp", "host", "action"]
    elif etype == "telephony":
        noconsume = ["timestamp", "host", "context"]
    elif etype == "authentication":
        noconsume = ["timestamp", "host", "eventtype"]
    else:
        return

    # Care for API v2
    if isinstance(duo_events, dict) and "authlogs" in duo_events:
        offset = duo_events["metadata"]["next_offset"]
        if offset is not None:
            state["{}_offset".format(etype)] = offset
        duo_events = duo_events["authlogs"]
        api_version = 2
    else:
        api_version = 1

    for e in duo_events:
        details = {}
        # Timestamp format: http://mozdef.readthedocs.io/en/latest/usage.html#mandatory-fields
        # Duo logs come as a UTC timestamp
        dt = datetime.utcfromtimestamp(e["timestamp"])
        mozmsg.timestamp = dt.replace(tzinfo=utc).isoformat()
        mozmsg.log["hostname"] = e["host"]
        for i in e:
            if i in noconsume:
                continue

            # Duo client doesn't translate inner dicts to dicts for some reason - its just a string, so we have to process and parse it
            if e[i] is not None and type(e[i]) == str and e[i].startswith("{"):
                j = json.loads(e[i])
                for x in j:
                    details[x] = j[x]
                continue

            details[i] = e[i]
        mozmsg.set_category(etype)
        localdetails = normalize(details)
        if "access_device" in localdetails:
            if "ip" in localdetails["access_device"]:
                localdetails["sourceipaddress"] = localdetails["access_device"]["ip"]
        mozmsg.details = localdetails
        del(localdetails)
        if etype == "administration":
            mozmsg.summary = e["action"]
        elif etype == "telephony":
            mozmsg.summary = e["context"]
        elif etype == "authentication":
            if api_version == 1:
                mozmsg.summary = (
                    e["eventtype"] + " " + e["result"] + " for " + e["username"]
                )
            else:
                mozmsg.summary = (
                    e["eventtype"] + " " + e["result"] + " for " + e["user"]["name"]
                )

        mozmsg.send()

    # last event timestamp record is stored and returned so that we can save our last position in the log.
    try:
        state[etype] = e["timestamp"]
    except UnboundLocalError:
        # duo_events was empty, no new event
        pass
    return state


def main():
    # FYI: This doesn't actually work yet, just mocking out as a mix of real-code and pseudo code
    api_call = UptycsRest(api_json_key=keyfile,
                          verify_ssl=verify_ssl,
                          suffix=options.DOMAIN,
                          api='/alerts',
                          method='GET',
                          post_data=None,
                          post_data_file=None)

    api_response = api_call.call_api()

    alerts = api_response['items']

    mozmsg = mozdef.MozDefEvent(options.MOZDEF_URL)
    mozmsg.tags = ["uptycs"]
    if options.update_tags != "":
        mozmsg.tags.append(options.update_tags)
    mozmsg.set_category("uptycs")
    mozmsg.source = "UptycsAPI"
    if options.DEBUG:
        mozmsg.debug = options.DEBUG
        mozmsg.set_send_to_syslog(True, only_syslog=True)

    # This will process events for all 3 log types and send them to MozDef. the state stores the last position in the
    # log when this script was last called.
    # NOTE: If administration and telephone logs support a "v2" API in the future it will most likely need to have the
    # same code with `next_offset` as authentication uses.
    process_events(
        mozmsg,
        duo.get_administrator_log(mintime=state["administration"] + 1),
        "administration",
        state,
    )


def initConfig():
    options.DOMAIN = getConfig("DOMAIN", "", options.configfile)
    options.USERID = getConfig("USERID", "", options.configfile)
    options.SECRET = getConfig("SECRET", "", options.configfile)
    options.CUSTOMERID = getConfig("CUSTOMERID", "", options.configfile)
    options.ID = getConfig("ID", "", options.configfile)
    options.KEY = getConfig("KEY", "", options.configfile)
    options.MOZDEF_URL = getConfig("MOZDEF_URL", "", options.configfile)
    options.DEBUG = getConfig("DEBUG", True, options.configfile)
    options.statepath = getConfig("statepath", "", options.configfile)
    options.update_tags = getConfig("addtag", "", options.configfile)


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
