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
import duo_client
import mozdef_client as mozdef
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
            if details[f] == "SUCCESS":
                normalized["success"] = True
            else:
                normalized["success"] = False
        normalized[f] = details[f]
    return normalized


def process_events(mozmsg, duo_events, etype, state):
    # There are some key fields that we use as MozDef fields, those are set to "noconsume"
    # After processing these fields, we just pour everything into the "details" fields of Mozdef, except for the
    # noconsume fields.

    if etype == 'administration':
        noconsume = ['timestamp', 'host', 'action']
    elif etype == 'telephony':
        noconsume = ['timestamp', 'host', 'context']
    elif etype == 'authentication':
        noconsume = ['timestamp', 'host', 'eventtype']
    else:
        return

    for e in duo_events:
        details = {}
        # Timestamp format: http://mozdef.readthedocs.io/en/latest/usage.html#mandatory-fields
        # Duo logs come as a UTC timestamp
        dt = datetime.utcfromtimestamp(e['timestamp'])
        mozmsg.timestamp = dt.replace(tzinfo=utc).isoformat()
        mozmsg.log['hostname'] = e['host']
        for i in e:
            if i in noconsume:
                continue

            # Duo client doesn't translate inner dicts to dicts for some reason - its just a string, so we have to process and parse it
            if e[i] is not None and type(e[i]) == str and e[i].startswith('{'):
                j = json.loads(e[i])
                for x in j:
                    details[x] = j[x]
                continue

            details[i] = e[i]
        mozmsg.set_category(etype)
        mozmsg.details = normalize(details)
        if etype == 'administration':
            mozmsg.summary = e['action']
        elif etype == 'telephony':
            mozmsg.summary = e['context']
        elif etype == 'authentication':
            mozmsg.summary = e['eventtype'] + ' ' + e['result'] + ' for ' + e['username']

        mozmsg.send()

    # last event timestamp record is stored and returned so that we can save our last position in the log.
    try:
        state[etype] = e['timestamp']
    except UnboundLocalError:
        # duo_events was empty, no new event
        pass
    return state


def main():
    try:
        state = pickle.load(open(options.statepath, 'rb'))
    except IOError:
        # Oh, you're new.
        state = {'administration': 0, 'authentication': 0, 'telephony': 0}

    duo = duo_client.Admin(ikey=options.IKEY, skey=options.SKEY, host=options.URL)
    mozmsg = mozdef.MozDefEvent(options.MOZDEF_URL)
    mozmsg.tags = ['duosecurity']
    if options.update_tags != '':
        mozmsg.tags.append(options.update_tags)
    mozmsg.set_category('authentication')
    mozmsg.source = 'DuoSecurityAPI'
    if options.DEBUG:
        mozmsg.debug = options.DEBUG
        mozmsg.set_send_to_syslog(True, only_syslog=True)

    # This will process events for all 3 log types and send them to MozDef. the state stores the last position in the
    # log when this script was last called.
    state = process_events(mozmsg, duo.get_administrator_log(mintime=state['administration'] + 1), 'administration', state)
    state = process_events(mozmsg, duo.get_authentication_log(mintime=state['authentication'] + 1), 'authentication', state)
    state = process_events(mozmsg, duo.get_telephony_log(mintime=state['telephony'] + 1), 'telephony', state)

    pickle.dump(state, open(options.statepath, 'wb'))


def initConfig():
    options.IKEY = getConfig('IKEY', '', options.configfile)
    options.SKEY = getConfig('SKEY', '', options.configfile)
    options.URL = getConfig('URL', '', options.configfile)
    options.MOZDEF_URL = getConfig('MOZDEF_URL', '', options.configfile)
    options.MOZDEF_URL = getConfig('MOZDEF_URL', '', options.configfile)
    options.DEBUG = getConfig('DEBUG', True, options.configfile)
    options.statepath = getConfig('statepath', '', options.configfile)
    options.update_tags = getConfig('addtag', '', options.configfile)


if __name__ == '__main__':
    parser = OptionParser()
    defaultconfigfile = sys.argv[0].replace('.py', '.conf')
    parser.add_option("-c",
                      dest='configfile',
                      default=defaultconfigfile,
                      help="configuration file to use")
    (options, args) = parser.parse_args()
    initConfig()
    main()
