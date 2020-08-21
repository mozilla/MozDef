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
import pickle
from jose import jwt, exceptions
from datetime import datetime, timedelta

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
        "admin_update_launch": {"event": "Auth0 Update Launched", "level": 1},
        "api_limit": {"event": "Rate Limit On API", "level": 4},
        "cls": {"event": "Code/Link Sent", "level": 0},
        "coff": {"event": "Connector Offline", "level": 3},
        "con": {"event": "Connector Online", "level": 1},
        "cs": {"event": "Code Sent", "level": 0},
        "depnote": {"event": "Deprecation Note", "level": 1},
        "du": {"event": "Deleted User", "level": 1},
        "f": {"event": "Failed Login", "level": 3},
        "fapi": {"event": "Failed API Operation", "level": 3},
        "fc": {"event": "Failed by Connector", "level": 3},
        "fce": {"event": "Failed Change Email", "level": 3},
        "fco": {"event": "Failed by CORS", "level": 3},
        "fcoa": {"event": "Failed Cross Origin Authentication", "level": 3},
        "fcp": {"event": "Failed Change Password", "level": 3},
        "fcph": {"event": "Failed Post Change Password Hook", "level": 3},
        "fcpn": {"event": "Failed Change Phone Number", "level": 3},
        "fcpr": {"event": "Failed Change Password Request", "level": 3},
        "fcpro": {"event": "Failed Connector Provisioning", "level": 4},
        "fcu": {"event": "Failed Change Username", "level": 3},
        "fd": {"event": "Failed Delegation", "level": 3},
        "fdeac": {"event": "Failed Device Activation", "level": 3},
        "fdeaz": {"event": "Failed Device Authorization Request", "level": 3},
        "fdecc": {"event": "User Canceled Device Confirmation", "level": 2},
        "fdu": {"event": "Failed User Deletion", "level": 3},
        "feacft": {"event": "Failed Exchange (Authorization Code for Access Token)", "level": 3},
        "feccft": {"event": "Failed Exchange (Client Credentials for Access Token)", "level": 1},
        "fede": {"event": "Failed Exchange (Device Code for Access Token)", "level": 3},
        "fens": {"event": "Failed Exchange (Native Social Login)", "level": 3},
        "feoobft": {"event": "Failed Exchange (Password and OOB Challenge for Access Token)", "level": 3},
        "feotpft": {"event": "Failed Exchange (Password and OTP Challenge for Access Token)", "level": 3},
        "fepft": {"event": "Failed Exchange (Password for Access Token)", "level": 3},
        "fercft": {"event": "Failed Exchange (Password and MFA Recovery code for Access Token)", "level": 3},
        "fertft": {"event": "Failed Exchange (Refresh Token for Access Token)", "level": 3},
        "flo": {"event": "Failed Logout", "level": 3},
        "fn": {"event": "Failed Sending Notification", "level": 3},
        "fp": {"event": "Failed Login (wrong password)", "level": 3},
        "fs": {"event": "Failed Signup", "level": 3},
        "fsa": {"event": "Failed Silent Auth", "level": 3},
        "fu": {"event": "Failed Login (invalid email/username)", "level": 3},
        "fui": {"event": "Failed users import", "level": 4},
        "fv": {"event": "Failed Verification Email", "level": 0},
        "fvr": {"event": "Failed Verification Email Request", "level": 3},
        "gd_auth_failed": {"event": "OTP Auth failed", "level": 3},
        "gd_auth_rejected": {"event": "OTP Auth rejected", "level": 3},
        "gd_auth_succeed": {"event": "OTP Auth success", "level": 1},
        "gd_enrollment_complete": {"event": "MFA Enrollment Complete", "level": 1},
        "gd_module_switch": {"event": "Module switch", "level": 1},
        "gd_otp_rate_limit_exceed": {"event": "Too many OTP failures", "level": 4},
        "gd_recovery_failed": {"event": "Failed Authentication using Recovery code.", "level": 3},
        "gd_recovery_rate_limit_exceed": {"event": "Failed Authentication using Recovery code too many times", "level": 4},
        "gd_recovery_succeed": {"event": "Success Authentication using Recovery code", "level": 1},
        "gd_send_pn": {"event": "Success Push notification for MFA sent", "level": 1},
        "gd_send_sms": {"event": "Success SMS for MFA sent", "level": 1},
        "gd_send_sms_failure": {"event": "Failed sending SMS for MFA", "level": 3},
        "gd_start_auth": {"event": "Second factor authentication event started for MFA", "level": 1},
        "gd_start_enroll": {"event": "Multi-factor authentication enroll has started", "level": 1},
        "gd_tenant_update": {"event": "Guardian tenant update", "level": 3},
        "gd_unenroll": {"event": "Device used for second factor authentication has been unenrolled", "level": 2},
        "gd_update_device_account": {"event": "Device used for second factor authentication has been updated", "level": 2},
        "gd_user_delete": {"event": "Deleted multi-factor user account", "level": 1},
        "limit_delegation": {"event": "Rate limit exceeded to /delegation endpoint", "level": 4},
        "limit_mu": {"event": "Blocked IP Address", "level": 3},
        "limit_ui": {"event": "Too Many Calls to /userinfo", "level": 4},
        "limit_wc": {"event": "Blocked Account", "level": 4},
        "pwd_leak": {"event": "User attempted to login with a leaked password", "level": 4},
        "s": {"event": "Success Login", "level": 1},
        "sapi": {"event": "Success API Operation", "level": 1},
        "sce": {"event": "Success Change Email", "level": 1},
        "scoa": {"event": "Success cross-origin authentication", "level": 1},
        "scp": {"event": "Success Change Password", "level": 1},
        "scph": {"event": "Success Post Change Password Hook", "level": 1},
        "scpn": {"event": "Success Change Phone Number", "level": 1},
        "scpr": {"event": "Success Change Password Request", "level": 0},
        "scu": {"event": "Success Change Username", "level": 1},
        "sd": {"event": "Success Delegation", "level": 3},
        "sdu": {"event": "Success User Deletion", "level": 1},
        "seacft": {"event": "Success Exchange (Authorization Code for Access Token)", "level": 1},
        "seccft": {"event": "Success Exchange (Client Credentials for Access Token)", "level": 1},
        "sede": {"event": "Successful Exchange (Device Code for Access Token)", "level": 1},
        "sens": {"event": "Success Exchange (Native Social Login)", "level": 1},
        "seoobft": {"event": "Success Exchange (Password and OOB Challenge for Access Token)", "level": 1},
        "seotpft": {"event": "Success Exchange (Password and OTP Challenge for Access Token)", "level": 1},
        "sepft": {"event": "Success Exchange (Password for Access Token)", "level": 1},
        "sercft": {"event": "Success Exchange (Password and MFA Recovery code for Access Token)", "level": 1},
        "sertft": {"event": "Success Exchange (Refresh Token for Access Token)", "level": 1},
        "slo": {"event": "Success Logout", "level": 1},
        "ss": {"event": "Success Signup", "level": 1},
        "ssa": {"event": "Success Silent Auth", "level": 1},
        "sui": {"event": "Success User Import", "level": 1},
        "sv": {"event": "Success Verification Email", "level": 0},
        "svr": {"event": "Success Verification Email Request", "level": 0},
        "sys_os_update_end": {"event": "Auth0 OS Update Ended", "level": 1},
        "sys_os_update_start": {"event": "Auth0 OS Update Started", "level": 1},
        "sys_update_end": {"event": "Auth0 Update Ended", "level": 1},
        "sys_update_start": {"event": "Auth0 Update Started", "level": 1},
        "ublkdu": {"event": "User block setup by anomaly detection has been released", "level": 3},
        "w": {"event": "Warnings During Login", "level": 2},
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
    authentication_words = ["Login", "Logout", "Silent", "Enrollment", "OTP", "Recovery", "Authentication", "Code", "Signup", "Push"]
    authorization_words = ["Authorization", "Access", "Delegation"]
    administration_words = ["API", "Operation", "Change", "Update", "Deleted", "unenrolled", "updated", "CORS", "Connector", "Blocked", "Breached", "Deletion", "block", "User", "released"]
    success_words = ["Success"]
    failed_words = ["Failed"]

    # fields that should always exist
    mozmsg.timestamp = msg.date
    details["messageid"] = msg._id
    details["sourceipaddress"] = msg.ip

    try:
        details["userid"] = msg.user_id
    except KeyError:
        pass

    try:
        if msg.user_name:
            details["username"] = msg.user_name
    except KeyError:
        pass

    try:
        # the details.request/response exist for api calls
        # but not for logins and other events
        # check and prefer them if present.
        if type(msg.details.response.body) is not list:
            details["action"] = msg.details.response.body.name
    except KeyError:
        pass

    try:
        if "email" in msg.details.response.body and msg.details.response.body.email is not None:
            details["email"] = msg.details.response.body.email
    except KeyError:
        pass

    try:
        details["useragent"] = msg.user_agent
    except KeyError:
        pass

    try:
        if msg.client_name:
            details["clientname"] = msg.client_name
    except KeyError:
        pass

    try:
        if msg.connection:
            details["connection"] = msg.connection
    except KeyError:
        pass

    try:
        if msg.client_id:
            details["clientid"] = msg.client_id
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
        if any(adminword in details["eventname"] for adminword in administration_words):
            mozmsg.set_category("administration")
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
        pass

    # set the summary
    # make summary be action/username (success login user@place.com)
    # if no details.username field exists we don't add it.

    # Build summary if neither email, description, nor username exists
    if 'eventname' in details:
        mozmsg.summary = "{event}".format(event=details.eventname)
        if 'description' in details and details['description'] != "None":
            mozmsg.summary += " {description}".format(event=details.eventname, description=details.description)
        if 'username' in details and details['username'] != "None":
            mozmsg.summary += " by {username}".format(username=details.username)
        if 'email' in details and details['email'] != "None":
            mozmsg.summary += " account: {email}".format(email=details.email)
        if 'clientname' in details and details['clientname'] != "None":
            mozmsg.summary += " to: {clientname}".format(clientname=details.clientname)

    # Get user data if present in response body
    try:
        if "multifactor" in msg.details.response.body and type(msg.details.response.body.multifactor) is list:
            details.mfa_provider = msg.details.response.body.multifactor
    except KeyError:
        pass

    try:
        if "ldap_groups" in msg.details.response.body and type(msg.details.response.body.ldap_groups) is list:
            details.ldap_groups = msg.details.response.body.ldap_groups
    except KeyError:
        pass

    try:
        if "last_ip" in msg.details.response.body and msg.details.response.body.last_ip is not None:
            details.user_last_known_ip = msg.details.response.body.last_ip
    except KeyError:
        pass

    try:
        if "last_login" in msg.details.response.body and msg.details.response.body.last_login is not None:
            details.user_last_login = msg.details.response.body.last_login
    except KeyError:
        pass

    # Differentiate auto login (session cookie check validated) from logged in and had password verified

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

    return mozmsg


def load_state(fpath):
    """Load last msg id we've read from auth0 (log index).
    @fpath string (path to state file)
    """
    try:
        state = pickle.load(open(fpath, "rb"))
    except IOError:
        # Oh, you're new.
        state = {
            'fromid': 0,
            'bearer': None,
        }
    return state


def save_state(fpath, state):
    """Saves last msg id we've read from auth0 (log index).
    @fpath string (path to state file)
    @state dict (state value)
    """
    pickle.dump(state, open(fpath, "wb"))


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
        "{url}/api/v2/logs?take={reqnr}&sort=date:1&per_page={reqnr}&from={fromid}&include_totals=true".format(
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
        # Because MozDef_Client doesn't support source, this will always be UNKNOWN as of 7/2020
        mozmsg.source = "auth0"
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
            traceback.print_exc()

        # Save raw initial message in final message
        # in case we ran into parsing errors
        mozmsg.details["raw_event"] = str(msg)

        mozmsg.send()

    if have_totals:
        return (int(ret["total"]), int(ret["start"]), int(ret["length"]), lastid)
    else:
        return (-1, -1, -1, lastid)


def fetch_new_bearer(config):
    data = {
        "client_id": config.auth0.client_id,
        "client_secret": config.auth0.client_secret,
        "audience": "{}/api/v2/".format(config.auth0.url),
        "grant_type": "client_credentials",
    }
    headers = {
        "content-type": "application/json"
    }
    resp = requests.post("{}/oauth/token".format(config.auth0.url), json=data, headers=headers)
    if not resp.ok:
        raise Exception(resp.text)

    resp_data = hjson.loads(resp.text)
    return resp_data['access_token']


def verify_bearer(bearer):
    # Verify the bearer token is not expired
    try:
        id_token = jwt.get_unverified_claims(token=bearer)
        token_expiry = datetime.fromtimestamp(id_token['exp'])
        # To ensure the bearer token doesn't run out during execution
        # we pad the time comparision with 30 minutes
        return (datetime.now() + timedelta(minutes=30)) < token_expiry
    except exceptions.JOSEError as e:
        logger.error("Unable to parse token : {} : {}".format(bearer, e))
        return False


def main():
    # Configuration loading
    config_location = os.path.dirname(sys.argv[0]) + "/" + "auth02mozdef.json"
    with open(config_location) as fd:
        config = DotDict(hjson.load(fd))

    if config is None:
        logger.error("No configuration file 'auth02mozdef.json' found.")
        sys.exit(1)

    state = load_state(config.state_file)
    # If bearer isn't set, reach out to auth0 for it
    if state['bearer'] is None:
        state['bearer'] = fetch_new_bearer(config)
    else:
        # Verify bearer token is still valid
        if not verify_bearer(state['bearer']):
            state['bearer'] = fetch_new_bearer(config)

    headers = {"Authorization": "Bearer {}".format(state['bearer']), "Accept": "application/json"}

    fromid = state['fromid']
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

    state['fromid'] = lastid
    save_state(config.state_file, state)


if __name__ == "__main__":
    main()
