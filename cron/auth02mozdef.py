#!/usr/bin/env python
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
# Copyright (c) 2016 Mozilla Corporation
# Author: gdestuynder@mozilla.com

# Imports auth0.com logs into MozDef

import hjson
import sys
import os
import requests
import mozdef_client as mozdef
try:
    import urllib.parse
    quote_url = urllib.parse.quote
except ImportError:
    #Well hello there python2 user!
    import urllib
    quote_url = urllib.quote
import traceback

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


# This is from https://auth0.com/docs/api/management/v2#!/Logs/get_logs
# and https://github.com/auth0/auth0-logs-to-logentries/blob/master/index.js (MIT)
# levels
#     0 = Debug
#     1 = Info
#     2 = Warning
#     3 = Error
#     4 = Critical
log_types=DotDict({
        's': {
            "event": 'Success Login',
            "level": 1
            },
        'slo': {
            "event": 'Success Logout',
            "level": 1
            },
        'flo': {
            "event": 'Failed Logout',
            "level": 3
            },
        'seacft': {
            "event": 'Success Exchange (Authorization Code for Access Token)',
            "level": 1
            },
        'feacft': {
            "event": 'Failed Exchange (Authorization Code for Access Token)',
            "level": 3
            },
        'f': {
            "event": 'Failed Login',
            "level": 3
            },
        'w': {
            "event": 'Warnings During Login',
            "level": 2
            },
        'du': {
            "event": 'Deleted User',
            "level": 1
            },
        'fu': {
            "event": 'Failed Login (invalid email/username)',
            "level": 3
            },
        'fp': {
            "event": 'Failed Login (wrong password)',
            "level": 3
            },
        'fc': {
            "event": 'Failed by Connector',
            "level": 3
            },
        'fco': {
            "event": 'Failed by CORS',
            "level": 3
            },
        'con': {
            "event": 'Connector Online',
            "level": 1
            },
        'coff': {
            "event": 'Connector Offline',
            "level": 3
            },
        'fcpro': {
            "event": 'Failed Connector Provisioning',
            "level": 4
            },
        'ss': {
                "event": 'Success Signup',
                "level": 1
                },
        'fs': {
                "event": 'Failed Signup',
                "level": 3
                },
        'cs': {
                "event": 'Code Sent',
                "level": 0
                },
        'cls': {
                "event": 'Code/Link Sent',
                "level": 0
                },
        'sv': {
                "event": 'Success Verification Email',
                "level": 0
                },
        'fv': {
                "event": 'Failed Verification Email',
                "level": 0
                },
        'scp': {
                "event": 'Success Change Password',
                "level": 1
                },
        'fcp': {
                "event": 'Failed Change Password',
                "level": 3
                },
        'sce': {
                "event": 'Success Change Email',
                "level": 1
                },
        'fce': {
                "event": 'Failed Change Email',
                "level": 3
                },
        'scu': {
                "event": 'Success Change Username',
                "level": 1
                },
        'fcu': {
                "event": 'Failed Change Username',
                "level": 3
                },
        'scpn': {
                "event": 'Success Change Phone Number',
                "level": 1
                },
        'fcpn': {
                "event": 'Failed Change Phone Number',
                "level": 3
                },
        'svr': {
                "event": 'Success Verification Email Request',
                "level": 0
                },
        'fvr': {
                "event": 'Failed Verification Email Request',
                "level": 3
                },
        'scpr': {
                "event": 'Success Change Password Request',
                "level": 0
                },
        'fcpr': {
                "event": 'Failed Change Password Request',
                "level": 3
                },
        'fn': {
                "event": 'Failed Sending Notification',
                "level": 3
                },
        'sapi': {
                "event": 'API Operation',
                "level": 1
                },
        'fapi': {
                "event": 'Failed API Operation',
                "level": 3
                },
        'limit_wc': {
                "event": 'Blocked Account',
                "level": 4
                },
        'limit_ui': {
                "event": 'Too Many Calls to /userinfo',
                "level": 4
                },
        'api_limit': {
                "event": 'Rate Limit On API',
                "level": 4
                },
        'sdu': {
                "event": 'Successful User Deletion',
                "level": 1
                },
        'fdu': {
                "event": 'Failed User Deletion',
                "level": 3
                },
        'sd': {
                "event": 'Success Delegation',
                "level": 3
         },
        'fd': {
                "event": 'Failed Delegation',
                "level": 3
         },
        'seccft': {
                "event": "Success Exchange (Client Credentials for Access Token)",
                "level": 1
        },
        'feccft': {
                "event": "Failed Exchange (Client Credentials for Access Token)",
                "level": 1
        },
        'fsa': {
                "event": "Failed Silent Auth",
                "level": 3
        },
        'ssa': {
                "event": "Success Silent Auth",
                "level": 1
        },
        'fepft': {
                "event": "Failed Exchange (Password for Access Token)",
                "level": 3
        },
        'limit_mu': {
                "event": "Blocked IP Address",
                "level": 3
        },
        'sepft': {
                "event": "Success Exchange (Password for Access Token)",
                "level": 1
        },
        'fcoa': {
                "event": "Failed Cross Origin Authentication",
                "level": 3
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

    try:
        details['type'] = log_types[msg.type].event
    except KeyError:
        #New message type, check https://manage-dev.mozilla.auth0.com/docs/api/management/v2#!/Logs/get_logs for ex.
        debug('New auth0 message type, please add support: {}'.format(msg.type))
        details['type'] = msg.type

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

    try:
        details['connection'] = msg.connection
    except KeyError:
        pass

    try:
        details['auth0_client_id'] = msg.client_id
    except KeyError:
        pass

    try:
        details['username'] = msg.details.request.auth.user.name
        details['action'] = msg.details.response.body.name
    except KeyError:
        try:
            details['error'] = 'true'
            details['errormsg'] = msg.details.error.message
        except KeyError:
            pass
        except AttributeError:
            pass
        try:
            details['username'] = msg.user_name
        except KeyError:
            pass

    # Differenciate auto login (session cookie check validated) from logged in and had password verified

    try:
        for i in msg.details.prompt:
            # Session cookie check
            if i.get('name') == 'authenticate':
                details['auth_type'] = 'Login succeeded due to a valid session cookie being supplied'
            elif i.get('name') == 'lock-password-authenticate':
                details['auth_type'] = 'Login succeeded due to a valid plaintext password being supplied'
    except KeyError:
        pass

    mozmsg.summary = "{mtype} {desc}".format(
        mtype=details.type,
        desc=details.description
    )

    mozmsg.details = details
    mozmsg.details['auth0_raw'] = str(msg)

    return mozmsg

def load_state(fpath):
    """Load last msg id we've read from auth0 (log index).
    @fpath string (path to state file)
    """
    state = 0
    try:
        with open(fpath) as fd:
            state = fd.read().split('\n')[0]
    except IOError:
        pass
    return state

def save_state(fpath, state):
    """Saves last msg id we've read from auth0 (log index).
    @fpath string (path to state file)
    @state int (state value)
    """
    with open(fpath, mode='w') as fd:
        fd.write(str(state)+'\n')

def byteify(input):
    """Convert input to ascii"""
    if isinstance(input, dict):
        return {byteify(key): byteify(value)
                for key, value in input.iteritems()}
    elif isinstance(input, list):
        return [byteify(element) for element in input]
    elif isinstance(input, unicode):
        return input.encode('utf-8')
    else:
        return input

def fetch_auth0_logs(config, headers, fromid):
    lastid = fromid

    r = requests.get('{url}?take={reqnr}&sort=date:1&per_page={reqnr}&include_totals=true&from={fromid}'.format(
        url=config.auth0.url,
        reqnr=config.auth0.reqnr,
        fromid=fromid),
        headers=headers)

    #If we fail here, auth0 is not responding to us the way we expected it
    if (not r.ok):
        raise Exception(r.url, r.reason, r.status_code, r.json())
    ret = r.json()

    #Sometimes API give us the requested totals.. sometimes not.
    if (type(ret) is dict) and ('logs' in ret.keys()):
        have_totals = True
        all_msgs = ret['logs']
    else:
        have_totals = False
        all_msgs = ret

    #Process all new auth0 log msgs, normalize and send them to mozdef
    for msg in all_msgs:
        mozmsg = mozdef.MozDefEvent(config.mozdef.url)
        if config.DEBUG == 'True':
            mozmsg.set_send_to_syslog(True, only_syslog=True)
        mozmsg.hostname = config.auth0.url
        mozmsg.tags = ['auth0']
        msg = byteify(msg)
        msg = DotDict(msg)
        lastid = msg._id

        #Fill in mozdef msg fields from the auth0 msg
        try:
            mozmsg = process_msg(mozmsg, msg)
        except KeyError as e:
            #if this happens the msg was malformed in some way
            mozmsg.details['error'] = 'true'
            mozmsg.details['errormsg'] = '"'+str(e)+'"'
            mozmsg.summary = 'Failed to parse auth0 message'
            if config.DEBUG == 'True':
                traceback.print_exc()
        mozmsg.send()

    if have_totals:
        return (int(ret['total']), int(ret['start']), int(ret['length']), lastid)
    else:
        return (0, 0, 0, lastid)


def main():
    # Configuration loading
    config_location = os.path.dirname(sys.argv[0]) + '/' + 'auth02mozdef.json'
    with open(config_location) as fd:
        config = DotDict(hjson.load(fd))

    if config is None:
        print("No configuration file 'auth02mozdef.json' found.")
        sys.exit(1)

    headers = {'Authorization': 'Bearer {}'.format(config.auth0.token),
            'Accept': 'application/json'}

    fromid = load_state(config.state_file)
    # Auth0 will interpret a 0 state as an error on our hosted instance, but will accept an empty parameter "as if it was 0"
    if (fromid == 0 or fromid == "0"):
        fromid = ""
    totals = 1
    start = 0
    length = 0

    # Fetch until we've gotten all messages
    while (totals > start+length):
        (totals, start, length, lastid) = fetch_auth0_logs(config, headers, fromid)
        fromid = lastid

    save_state(config.state_file, lastid)


if __name__ == "__main__":
    main()
