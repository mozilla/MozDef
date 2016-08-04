#!/usr/bin/env python
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
# Copyright (c) 2016 Mozilla Corporation
# Author: gdestuynder@mozilla.com

# Imports auth0.com logs into MozDef

import hjson
import sys
import requests
import mozdef_client as mozdef
try:
    import urllib.parse
    quote_url = urllib.parse.quote
except ImportError:
    #Well hello there python2 user!
    import urllib
    quote_url = urllib.quote

class DotDict(dict):
    '''dict.item notation for dict()'s'''
    __getattr__ = dict.__getitem__
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__

    def __init__(self, dct):
        for key, value in dct.items():
            if hasattr(value, 'keys'):
                value = DotDict(value)
            self[key] = value

def fatal(msg):
    print(msg)
    sys.exit(1)

def debug(msg):
    sys.stderr.write('+++ {}\n'.format(msg))

#This is from https://auth0.com/docs/api/management/v2#!/Logs/get_logs
#and https://github.com/auth0/auth0-logs-to-logentries/blob/master/index.js (MIT)
log_types=DotDict({
        's': {
            "event": 'Success Login',
            "level": 1 # Info
            },
        'seacft': {
            "event": 'Success Exchange',
            "level": 1 # Info
            },
        'feacft': {
            "event": 'Failed Exchange',
            "level": 3 # Error
            },
        'f': {
            "event": 'Failed Login',
            "level": 3 # Error
            },
        'w': {
            "event": 'Warnings During Login',
            "level": 2 # Warning
            },
        'du': {
            "event": 'Deleted User',
            "level": 1 # Info
            },
        'fu': {
            "event": 'Failed Login (invalid email/username)',
            "level": 3 # Error
            },
        'fp': {
            "event": 'Failed Login (wrong password)',
            "level": 3 # Error
            },
        'fc': {
            "event": 'Failed by Connector',
            "level": 3 # Error
            },
        'fco': {
            "event": 'Failed by CORS',
            "level": 3 # Error
            },
        'con': {
            "event": 'Connector Online',
            "level": 1 # Info
            },
        'coff': {
            "event": 'Connector Offline',
            "level": 3 # Error
            },
        'fcpro': {
            "event": 'Failed Connector Provisioning',
            "level": 4 # Critical
            },
        'ss': {
                "event": 'Success Signup',
                "level": 1 # Info
                },
        'fs': {
                "event": 'Failed Signup',
                "level": 3 # Error
                },
        'cs': {
                "event": 'Code Sent',
                "level": 0 # Debug
                },
        'cls': {
                "event": 'Code/Link Sent',
                "level": 0 # Debug
                },
        'sv': {
                "event": 'Success Verification Email',
                "level": 0 # Debug
                },
        'fv': {
                "event": 'Failed Verification Email',
                "level": 0 # Debug
                },
        'scp': {
                "event": 'Success Change Password',
                "level": 1 # Info
                },
        'fcp': {
                "event": 'Failed Change Password',
                "level": 3 # Error
                },
        'sce': {
                "event": 'Success Change Email',
                "level": 1 # Info
                },
        'fce': {
                "event": 'Failed Change Email',
                "level": 3 # Error
                },
        'scu': {
                "event": 'Success Change Username',
                "level": 1 # Info
                },
        'fcu': {
                "event": 'Failed Change Username',
                "level": 3 # Error
                },
        'scpn': {
                "event": 'Success Change Phone Number',
                "level": 1 # Info
                },
        'fcpn': {
                "event": 'Failed Change Phone Number',
                "level": 3 # Error
                },
        'svr': {
                "event": 'Success Verification Email Request',
                "level": 0 # Debug
                },
        'fvr': {
                "event": 'Failed Verification Email Request',
                "level": 3 # Error
                },
        'scpr': {
                "event": 'Success Change Password Request',
                "level": 0 # Debug
                },
        'fcpr': {
                "event": 'Failed Change Password Request',
                "level": 3 # Error
                },
        'fn': {
                "event": 'Failed Sending Notification',
                "level": 3 # Error
                },
        'sapi': {
                "event": 'API Operation',
                "level": 1 #Info
                },
        'fapi': {
                "event": 'Failed API Operation',
                "level": 3 #Error
                },
        'limit_wc': {
                "event": 'Blocked Account',
                "level": 4 # Critical
                },
        'limit_ui': {
                "event": 'Too Many Calls to /userinfo',
                "level": 4 # Critical
                },
        'api_limit': {
                "event": 'Rate Limit On API',
                "level": 4 #Critical
                },
        'sdu': {
                "event": 'Successful User Deletion',
                "level": 1 # Info
                },
        'fdu': {
                "event": 'Failed User Deletion',
                "level": 3 # Error
                }
})

def process_msg(mozmsg, msg):
    """Normalization function for auth0 msg.
    @mozmsg: MozDefEvent (mozdef message)
    @msg: DotDict (json with auth0 raw message data).

    All the try-except loops handle cases where the auth0 msg may or may not contain expected fields.
    The msg structure is not garanteed.
    See also https://auth0.com/docs/api/management/v2#!/Logs/get_logs
    """
    details = DotDict({})

    try:
        mozmsg.useragent = msg.user_agent
    except KeyError:
        pass

    details['type'] = log_types[msg.type].event
    if log_types[msg.type].level == 3:
        mozmsg.set_severity(mozdef.MozDefEvent.SEVERITY_ERROR)
    elif log_types[msg.type].level > 3:
        mozmsg.set_severity(mozdef.MozDefEvent.SEVERITY_CRITICAL)
    details['sourceipaddress'] = msg.ip

    try:
        details['description'] = msg.description
    except KeyError:
        details['description'] = ""

    mozmsg.timestamp = msg.date
    details['auth0_msg_id'] = msg._id

    try:
        details['auth0_client'] = msg.client_name
    except KeyError:
        pass

    details['auth0_client_id'] = msg.client_id

    try:
        details['username'] = msg.details.request.auth.user
        details['action'] = msg.details.response.body.name
    except KeyError:
        try:
            details['errormsg'] = msg.details.error.message
            details['error'] = 'true'
        except KeyError:
            pass
        details['username'] = msg.user_name

    try:
        auth0details = msg.details.details
    except KeyError:
        auth0details = ""

    mozmsg.summary = "{type} {desc} {auth0details}".format(type=details.type, desc=details.description,
            auth0details=auth0details)
    mozmsg.details = details
    #that's just too much data, IMO
    #mozmsg.details['auth0_raw'] = msg
    return mozmsg

def load_state(fpath):
    """Load last msg id we've read from auth0 (log index).
    @fpath string (path to state file)
    """
    state = 0
    try:
        with open(fpath) as fd:
            state = int(fd.read().split('\n')[0])
    except FileNotFoundError:
        pass
    return state

def save_state(fpath, state):
    """Saves last msg id we've read from auth0 (log index).
    @fpath string (path to state file)
    @state int (state value)
    """
    with open(fpath, mode='w') as fd:
        fd.write(str(state)+'\n')

def main():
    #Configuration loading
    with open('auth02mozdef.json') as fd:
        config = DotDict(hjson.load(fd))

    if config == None:
        print("No configuration file 'auth02mozdef.json' found.")
        sys.exit(1)

    headers = {'Authorization': 'Bearer {}'.format(config.auth0.token),
            'Accept': 'application/json'}

    fromid = load_state(config.state_file)

    r = requests.get('{url}?take={reqnr}&sort=date:1&per_page={reqnr}&include_totals=true&from={fromid}'.format(
        url=config.auth0.url,
        reqnr=config.auth0.reqnr,
        fromid=fromid),
        headers=headers)

    #If we fail here, auth0 is not responding to us the way we expected it
    if (not r.ok):
        raise Exception(r.url, r.reason, r.status_code, r.json())
    ret = r.json()

    #Process all new auth0 log msgs, normalize and send them to mozdef
    for msg in ret:
        mozmsg = mozdef.MozDefEvent(config.mozdef.url)
        if config.DEBUG:
            mozmsg.set_send_to_syslog(True, only_syslog=True)
        mozmsg.source = config.auth0.url
        mozmsg.tags = ['auth0']
        msg = DotDict(msg)
        lastid = msg._id

        #Fill in mozdef msg fields from the auth0 msg
        try:
            mozmsg = process_msg(mozmsg, msg)
        except KeyError as e:
            #if this happens the msg was malformed in some way
            mozmsg.details['error'] = 'true'
            mozmsg.details['errormsg'] = e
            mozmsg.summary = 'Failed to parse auth0 message'
        mozmsg.send()

    save_state(config.state_file, lastid)

if __name__ == "__main__":
    main()
