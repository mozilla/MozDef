# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# Copyright (c) 2014 Mozilla Corporation

from enum import Enum
import os
from typing import NamedTuple, Optional, Tuple

import hjson


CONFIG_FILE = os.path.join(os.path.dirname(__file__), 'triage_bot.json')


class AlertLabel(Enum):
    '''Enumerates each of the alerts supported by the triage bot.
    '''

    SENSITIVE_HOST_SESSION = 'sensitive_host_session'
    DUO_BYPASS_CODES_USED = 'duo_bypass_codes_used'
    DUO_BYPASS_CODES_GENERATED = 'duo_bypass_codes_generated'
    SSH_ACCESS_SIGN_RELENG = 'ssh_access_sign_releng'

# TODO: Change to a dataclass when Python 3.7+ is adopted.

Email = str

class AlertTriageRequest(NamedTuple):
    '''A message bound for the AWS lambda function that interfaces with Slack.
    '''

    identifier: str
    alert: AlertLabel
    summary: str
    user: Email


class message(object):
    '''The main interface to the alert action.
    '''

    def __init__(self):
        '''Loads the configuration for the action and announces which alerts
        the action can be run against.
        '''

        with open(CONFIG_FILE) as cfg_file:
            self._config = hjson.load(cfg_file)

        self.registration = '*'
        self.priority = 1


    def onMessage(self, message):
        '''The main entrypoint to the alert action invoked with a message
        describing an alert.
        '''

        return message


def try_make_outbound(message) -> Optional[AlertTriageRequest]:
    '''Attempt to determine the kind of alert contained in `message` in
    order to produce an `AlertTriageRequest` destined for the web server comp.
    '''

    return None
