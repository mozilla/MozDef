#!/usr/bin/env python
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
#

import sys
import json
import duo_client
import mozdef_client as mozdef
import pickle
from configlib import getConfig, OptionParser
from mozdef_util.utilities.toUTC import toUTC


def normalize(details):
    # Normalizes fields to conform to http://mozdef.readthedocs.io/en/latest/usage.html#mandatory-fields
    # This is mainly used for common field names to put inside the details structure
    # There might be faster ways to do this
    normalized = {}

    for f in details:
        if f in ("ip", "ip_address", "client_ip"):
            normalized["sourceipaddress"] = details[f]
            continue
        if f in ("eventtype", "event_type"):
            normalized["eventtype"] = details[f]
            continue
        if f in ("host", "hostname"):
            normalized["hostname"] = details[f]
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


def process_events(mozmsg, duo_events, etype, state):
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
        noconsume = ["timestamp", "host", "event_type"]
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
        if 'timestamp' in e:
            mozmsg.timestamp = toUTC(e['timestamp']).isoformat()
        # mozdef_client sets hostname to the host that the client runs on,
        # so we'll set the clientname in this cron to be the host we pulled from.
        if 'host' in e and not None:
            mozmsg.log["hostname"] = e["host"]
        if 'hostname' in e and not None:
            mozmsg.log["hostname"] = e["hostname"]
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
            if "hostname" in localdetails["access_device"]:
                if localdetails["access_device"]["hostname"] is None:
                    del localdetails["access_device"]["hostname"]
        mozmsg.details = localdetails
        del(localdetails)
        mozmsg.hostname = options.URL
        if etype == "administration":
            if 'error' in e:
                mozmsg.summary = (
                    e["action"] + " because of " + e["error"] + " by " + e["username"]
                )
            else:
                mozmsg.summary = (
                    e["action"] + " by " + e["username"]
                )
        elif etype == "telephony":
            mozmsg.summary = e["context"]
        elif etype == "authentication":
            if api_version == 1:
                mozmsg.summary = (
                    e["eventtype"] + " " + e["result"] + " for " + e["username"]
                )
            else:
                if 'reason' in e and e['reason'] is not None:
                    mozmsg.summary = (
                        e["eventtype"] + " " + e["result"] + " for " + e["user"]["name"] + " due to " + e["reason"]
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
    try:
        state = pickle.load(open(options.statepath, "rb"))
    except IOError:
        # Oh, you're new.
        # Note API v2 expect full, correct and within range timestamps in millisec so we start recently
        # API v1 uses normal timestamps in seconds instead
        state = {
            "administration": 0,
            "administration_offset": None,
            "authentication": 1547000000000,
            "authentication_offset": None,
            "telephony": 0,
            "telephony_offset": None,
        }

    # Convert v1 (sec) timestamp to v2 (ms)...
    if state["authentication"] < 1547000000000:
        state["authentication"] = int(str(state["authentication"]) + "000")

    duo = duo_client.Admin(ikey=options.IKEY, skey=options.SKEY, host=options.URL)
    mozmsg = mozdef.MozDefEvent(options.MOZDEF_URL)
    mozmsg.tags = ["duosecurity"]
    if options.update_tags != "":
        mozmsg.tags.append(options.update_tags)
    mozmsg.set_category("authentication")
    mozmsg.source = "DuoSecurityAPI"
    if options.DEBUG:
        mozmsg.debug = options.DEBUG
        mozmsg.set_send_to_syslog(True, only_syslog=True)

    # This will process events for all 3 log types and send them to MozDef. the state stores the last position in the
    # log when this script was last called.
    # NOTE: If administration and telephone logs support a "v2" API in the future it will most likely need to have the
    # same code with `next_offset` as authentication uses.
    state = process_events(
        mozmsg,
        duo.get_administrator_log(mintime=state["administration"] + 1),
        "administration",
        state,
    )
    state = process_events(
        mozmsg,
        duo.get_authentication_log(
            api_version=2,
            limit="1000",
            sort="ts:asc",
            mintime=state["authentication"] + 1,
            next_offset=state["authentication_offset"],
        ),
        "authentication",
        state,
    )
    state = process_events(
        mozmsg,
        duo.get_telephony_log(mintime=state["telephony"] + 1),
        "telephony",
        state,
    )

    pickle.dump(state, open(options.statepath, "wb"))


def initConfig():
    options.IKEY = getConfig("IKEY", "", options.configfile)
    options.SKEY = getConfig("SKEY", "", options.configfile)
    options.URL = getConfig("URL", "", options.configfile)
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
