#!/usr/bin/env python
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# Copyright (c) 2016 Mozilla Corporation

# Imports auth0.com logs into MozDef

import hjson
import sys
import os
import requests
import traceback

import mozdef_client as mozdef

from mozdef_util.utilities.dot_dict import DotDict
from mozdef_util.utilities.logger import logger


def fatal(msg):
    print(msg)
    sys.exit(1)


# This is from https://auth0.com/docs/api/management/v2#!/Logs/get_logs
# auth0 calls these events with an acronym and description
# The logs have the acronym, but not the description
# but do include a 'description' field that is additional detailed words
# about what happened.
# See also: https://auth0.com/docs/logs#log-data-event-listing
# levels
#     0 = Debug
#     1 = Info
#     2 = Warning
#     3 = Error
#     4 = Critical
log_types = DotDict(
    {
        "s": {"event": "Success Login", "level": 1},
        "slo": {"event": "Success Logout", "level": 1},
        "flo": {"event": "Failed Logout", "level": 3},
        "seacft": {"event": "Success Exchange (Authorization Code for Access Token)", "level": 1},
        "feacft": {"event": "Failed Exchange (Authorization Code for Access Token)", "level": 3},
        "f": {"event": "Failed Login", "level": 3},
        "w": {"event": "Warnings During Login", "level": 2},
        "du": {"event": "Deleted User", "level": 1},
        "fu": {"event": "Failed Login (invalid email/username)", "level": 3},
        "fp": {"event": "Failed Login (wrong password)", "level": 3},
        "fc": {"event": "Failed by Connector", "level": 3},
        "fco": {"event": "Failed by CORS", "level": 3},
        "con": {"event": "Connector Online", "level": 1},
        "coff": {"event": "Connector Offline", "level": 3},
        "fcpro": {"event": "Failed Connector Provisioning", "level": 4},
        "ss": {"event": "Success Signup", "level": 1},
        "fs": {"event": "Failed Signup", "level": 3},
        "cs": {"event": "Code Sent", "level": 0},
        "cls": {"event": "Code/Link Sent", "level": 0},
        "sv": {"event": "Success Verification Email", "level": 0},
        "fv": {"event": "Failed Verification Email", "level": 0},
        "scp": {"event": "Success Change Password", "level": 1},
        "fcp": {"event": "Failed Change Password", "level": 3},
        "sce": {"event": "Success Change Email", "level": 1},
        "fce": {"event": "Failed Change Email", "level": 3},
        "scu": {"event": "Success Change Username", "level": 1},
        "fcu": {"event": "Failed Change Username", "level": 3},
        "scpn": {"event": "Success Change Phone Number", "level": 1},
        "fcpn": {"event": "Failed Change Phone Number", "level": 3},
        "svr": {"event": "Success Verification Email Request", "level": 0},
        "fvr": {"event": "Failed Verification Email Request", "level": 3},
        "scpr": {"event": "Success Change Password Request", "level": 0},
        "fcpr": {"event": "Failed Change Password Request", "level": 3},
        "fn": {"event": "Failed Sending Notification", "level": 3},
        "sapi": {"event": "API Operation", "level": 1},
        "fapi": {"event": "Failed API Operation", "level": 3},
        "limit_wc": {"event": "Blocked Account", "level": 4},
        "limit_ui": {"event": "Too Many Calls to /userinfo", "level": 4},
        "api_limit": {"event": "Rate Limit On API", "level": 4},
        "sdu": {"event": "Successful User Deletion", "level": 1},
        "fdu": {"event": "Failed User Deletion", "level": 3},
        "sd": {"event": "Success Delegation", "level": 3},
        "fd": {"event": "Failed Delegation", "level": 3},
        "seccft": {"event": "Success Exchange (Client Credentials for Access Token)", "level": 1},
        "feccft": {"event": "Failed Exchange (Client Credentials for Access Token)", "level": 1},
        "fsa": {"event": "Failed Silent Auth", "level": 3},
        "ssa": {"event": "Success Silent Auth", "level": 1},
        "fepft": {"event": "Failed Exchange (Password for Access Token)", "level": 3},
        "limit_mu": {"event": "Blocked IP Address", "level": 3},
        "sepft": {"event": "Success Exchange (Password for Access Token)", "level": 1},
        "fcoa": {"event": "Failed Cross Origin Authentication", "level": 3},
        "depnote": {"event": "Deprecation Note", "level": 1},
    }
)


def process_msg(mozmsg, msg):
    """Normalization function for auth0 msg.
    @mozmsg: MozDefEvent (mozdef message as DotDict)
    @msg: DotDict (json with auth0 raw message data).

    All the try-except loops handle cases where the auth0 msg may or may not contain expected fields.
    The msg structure is not garanteed.
    See also https://auth0.com/docs/api/management/v2#!/Logs/get_logs
    """
    details = DotDict({})

    # key words used to set category and success/failure markers
    authentication_words = ["Login", "Logout", "Auth"]
    authorization_words = ["Authorization", "Access", "Delegation"]
    success_words = ["Success"]
    failed_words = ["Failed"]

    # default category (might be modified below to be more specific)
    mozmsg.set_category("iam")
    mozmsg.source = "auth0"
    # fields that should always exist
    mozmsg.timestamp = msg.date
    details["messageid"] = msg._id
    details["sourceipaddress"] = msg.ip

    try:
        details["userid"] = msg.user_id
    except KeyError:
        pass

    try:
        details["username"] = msg.user_name
    except KeyError:
        pass

    try:
        # the details.request/response exist for api calls
        # but not for logins and other events
        # check and prefer them if present.
        details["username"] = msg.details.request.auth.user.name
        if type(msg.details.response.body) is not list:
            details["action"] = msg.details.response.body.name
    except KeyError:
        pass

    try:
        details["useragent"] = msg.user_agent
    except KeyError:
        pass

    try:
        # auth0 calls these events with an acronym and name
        details["eventname"] = log_types[msg.type].event
        # determine the event category
        if any(authword in details["eventname"] for authword in authentication_words):
            mozmsg.set_category("authentication")
        if any(authword in details["eventname"] for authword in authorization_words):
            mozmsg.set_category("authorization")
        # determine success/failure
        if any(failword in details["eventname"] for failword in failed_words):
            details.success = False
        if any(successword in details["eventname"] for successword in success_words):
            details.success = True
    except KeyError:
        # New message type, check https://manage-dev.mozilla.auth0.com/docs/api/management/v2#!/Logs/get_logs for ex.
        logger.error("New auth0 message type, please add support: {}".format(msg.type))
        details["eventname"] = msg.type

    # determine severity level
    if log_types[msg.type].level == 3:
        mozmsg.set_severity(mozdef.MozDefEvent.SEVERITY_ERROR)
    elif log_types[msg.type].level > 3:
        mozmsg.set_severity(mozdef.MozDefEvent.SEVERITY_CRITICAL)

    # default description
    details["description"] = ""
    try:
        if "description" in msg and msg.description is not None:
            # use the detailed description of the operation sent from auth0
            # Update a rule, add a site, update a site, etc
            details["description"] = msg.description
    except KeyError:
        details["description"] = ""

    # set the summary
    if "auth" in mozmsg._category:
        # make summary be action/username (success login user@place.com)
        # include UNKNOWN as username value in summary
        # if no details.username field exists
        tmp_username = "UNKNOWN"
        if 'username' in details:
            tmp_username = details.username
        mozmsg.summary = "{event} {username}".format(event=details.eventname, username=tmp_username)
    else:
        # default summary as action and description (if it exists)
        mozmsg.summary = "{event} {desc}".format(event=details.eventname, desc=details.description)

    try:
        details["clientname"] = msg.client_name
    except KeyError:
        pass

    try:
        details["connection"] = msg.connection
    except KeyError:
        pass

    try:
        details["clientid"] = msg.client_id
    except KeyError:
        pass

    # Differenciate auto login (session cookie check validated) from logged in and had password verified

    try:
        for i in msg.details.prompt:
            # Session cookie check
            if i.get("name") == "authenticate":
                details["authtype"] = "Login succeeded due to a valid session cookie being supplied"
            elif i.get("name") == "lock-password-authenticate":
                details["authtype"] = "Login succeeded due to a valid plaintext password being supplied"
    except KeyError:
        pass

    mozmsg.details = details
    mozmsg.details["raw"] = str(msg)

    return mozmsg


def load_state(fpath):
    """Load last msg id we've read from auth0 (log index).
    @fpath string (path to state file)
    """
    state = 0
    try:
        with open(fpath) as fd:
            state = fd.read().split("\n")[0]
    except IOError:
        pass
    return state


def save_state(fpath, state):
    """Saves last msg id we've read from auth0 (log index).
    @fpath string (path to state file)
    @state int (state value)
    """
    with open(fpath, mode="w") as fd:
        fd.write(str(state) + "\n")


def byteify(input):
    """Convert input to ascii"""
    if isinstance(input, dict):
        return {byteify(key): byteify(value) for key, value in input.items()}
    elif isinstance(input, list):
        return [byteify(element) for element in input]
    elif not isinstance(input, str):
        return str(input)
    else:
        return input


def fetch_auth0_logs(config, headers, fromid):
    lastid = fromid

    r = requests.get(
        "{url}?take={reqnr}&sort=date:1&per_page={reqnr}&from={fromid}&include_totals=true".format(
            url=config.auth0.url, reqnr=config.auth0.reqnr, fromid=fromid
        ),
        headers=headers,
    )

    # If we fail here, auth0 is not responding to us the way we expected it
    if not r.ok:
        raise Exception(r.url, r.reason, r.status_code, r.json())
    ret = r.json()

    # Sometimes API give us the requested totals.. sometimes not.
    # To be clear; totals are now only returned when using `page=..` and not using `from=..` parameters
    # The issue is that when using `page`, auth0 internally splices the log by page, which is extremely slow and the
    # call takes 10-20s to return each time.
    # When using `from` auth0 queries the index for that location which is fast, so we use `from`
    # this means we can't properly page results, so we have to "try to fetch" until no more logs are returned
    # Finally note that when using `from` the `sort` ordering is not guaranteed to work according to the API docs
    if type(ret) is dict and "logs" in ret:
        have_totals = True
        all_msgs = ret["logs"]
    else:
        have_totals = False
        all_msgs = ret

    # Process all new auth0 log msgs, normalize and send them to mozdef
    for msg in all_msgs:
        mozmsg = mozdef.MozDefEvent(config.mozdef.url)
        if config.DEBUG == "True":
            mozmsg.set_send_to_syslog(True, only_syslog=True)
        mozmsg.hostname = config.auth0.url
        mozmsg.tags = ["auth0"]
        msg = byteify(msg)
        msg = DotDict(msg)
        lastid = msg._id

        # Fill in mozdef msg fields from the auth0 msg
        try:
            mozmsg = process_msg(mozmsg, msg)
        except KeyError as e:
            # if this happens the msg was malformed in some way
            mozmsg.details["error"] = "true"
            mozmsg.details["errormsg"] = '"' + str(e) + '"'
            mozmsg.summary = "Failed to parse auth0 message"
            if config.DEBUG == "True":
                traceback.print_exc()
        mozmsg.send()

    if have_totals:
        return (int(ret["total"]), int(ret["start"]), int(ret["length"]), lastid)
    else:
        return (-1, -1, -1, lastid)


def main():
    # Configuration loading
    config_location = os.path.dirname(sys.argv[0]) + "/" + "auth02mozdef.json"
    with open(config_location) as fd:
        config = DotDict(hjson.load(fd))

    if config is None:
        logger.error("No configuration file 'auth02mozdef.json' found.")
        sys.exit(1)

    headers = {"Authorization": "Bearer {}".format(config.auth0.token), "Accept": "application/json"}

    fromid = load_state(config.state_file)
    # Auth0 will interpret a 0 state as an error on our hosted instance, but will accept an empty parameter "as if it was 0"
    if fromid == 0 or fromid == "0":
        fromid = ""
    totals = 1
    start = 0
    length = 0

    # Fetch until we've gotten all messages
    while totals > start + length:
        (totals, start, length, lastid) = fetch_auth0_logs(config, headers, fromid)

        if totals == -1:
            if fromid == lastid:
                # We got everything, we're done!
                break
        fromid = lastid

    save_state(config.state_file, lastid)


if __name__ == "__main__":
    main()
