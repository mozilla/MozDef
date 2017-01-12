#!/usr/bin/env python
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Contributors:
# Guillaume Destuynder kang@mozilla.com
# Brandon Myers bmyers@mozilla.com

import sys
import os
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../lib'))
from utilities.toUTC import toUTC


import sys
from configlib import getConfig, OptionParser
import json


import duo_client
import mozdef_client as mozdef
import pickle


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
        mozmsg.log['timestamp'] = toUTC(e['timestamp']).isoformat()
        mozmsg.log['hostname'] = e['host']
        for i in e:
            if i in noconsume:
                continue

    # Duo client doesn't translate inner dicts to dicts for some reason - its just a string, so we have to process and parse it
            if e[i] != None and type(e[i]) == str and  e[i].startswith('{'):
                j = json.loads(e[i])
                for x in j:
                    details[x] = j[x]
                continue

            details[i] = e[i]
        if etype == 'administration':
          mozmsg.send(e['action'], details=details)
        elif etype == 'telephony':
          mozmsg.send(e['context'], details=details)
        elif etype == 'authentication':
          mozmsg.send(e['eventtype']+' '+e['result']+' for '+e['username'], details=details)

    # last event timestamp record is stored and returned so that we can save our last position in the log.
    try:
        state[etype] = e['timestamp']
    except UnboundLocalError:
        # duo_events was empty, no new event
        pass
    return state



def main():
    state_location = os.path.dirname(sys.argv[0]) + '/' + options.statepath
    try:
        state = pickle.load(open(state_location, 'rb'))
    except IOError:
        # Oh, you're new.
        state = {'administration': 0, 'authentication': 0, 'telephony': 0}

    duo = duo_client.Admin(ikey=options.IKEY, skey=options.SKEY, host=options.URL)
    mozmsg = mozdef.MozDefMsg(options.MOZDEF_URL, tags=['duosecurity', 'logs'])
    mozmsg.debug = options.DEBUG



    # This will process events for all 3 log types and send them to MozDef. the state stores the last position in the
    # log when this script was last called.
    state = process_events(mozmsg, duo.get_administrator_log(mintime=state['administration']+1), 'administration', state)
    state = process_events(mozmsg, duo.get_authentication_log(mintime=state['authentication']+1), 'authentication', state)
    state = process_events(mozmsg, duo.get_telephony_log(mintime=state['telephony']+1), 'telephony', state)

    pickle.dump(state, open(state_location, 'wb'))


def initConfig():
    options.IKEY = getConfig('IKEY', '', options.configfile)
    options.SKEY = getConfig('SKEY', '', options.configfile)
    options.URL = getConfig('URL', '', options.configfile)
    options.MOZDEF_URL = getConfig('MOZDEF_URL', '', options.configfile)
    options.MOZDEF_URL = getConfig('MOZDEF_URL', '', options.configfile)
    options.DEBUG = getConfig('DEBUG', True, options.configfile)
    options.statepath = getConfig('statepath', '', options.configfile)


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
