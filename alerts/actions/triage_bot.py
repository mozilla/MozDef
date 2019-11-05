# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# Copyright (c) 2014 Mozilla Corporation

from enum import Enum
import os
from typing import Any, Dict, NamedTuple, Optional, Tuple

import hjson


CONFIG_FILE = os.path.join(os.path.dirname(__file__), 'triage_bot.json')

Alert = Dict[Any, Any]

Email = str


class AlertLabel(Enum):
    '''Enumerates each of the alerts supported by the triage bot.
    '''

    SENSITIVE_HOST_SESSION = 'sensitive_host_session'
    DUO_BYPASS_CODES_USED = 'duo_bypass_codes_used'
    DUO_BYPASS_CODES_GENERATED = 'duo_bypass_codes_generated'
    SSH_ACCESS_SIGN_RELENG = 'ssh_access_sign_releng'

# TODO: Change to a dataclass when Python 3.7+ is adopted.

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

        request = try_make_outbound(message)

        if request is not None:
            self._test_flag = True
            print(request)

        return message


def try_make_outbound(message: Alert) -> Optional[AlertTriageRequest]:
    '''Attempt to determine the kind of alert contained in `message` in
    order to produce an `AlertTriageRequest` destined for the web server comp.
    '''

    _source = message.get('_source', {})
    category = _source.get('category')
    tags = _source.get('tags', [])

    is_sensitive_host_access = 'session' in tags and category  == 'session'

    is_duo_codes_generated = 'duosecurity' in tags and category == 'duo' and\
        'codes generated' in _source.get('summary', '')

    is_duo_bypass_codes_used = 'duo_bypass_codes_used' in tags and\
        category == 'bypassused'

    is_ssh_access_releng = 'ssh' in tags and category == 'access'

    if is_sensitive_host_access:
        return _make_sensitive_host_access(message)

    if is_duo_codes_generated:
        return _make_duo_code_gen(message)

    if is_duo_bypass_codes_used:
        return _make_duo_code_used(message)

    if is_ssh_access_releng:
        return _make_ssh_access_releng(message)

    return None


def _make_sensitive_host_access(alert: Alert) -> Optional[AlertTriageRequest]:
    null = {
        'documentsource': {
            'details': {
                'username': None
            }
        }
    }

    _source = alert.get('_source', {})
    _events = _source.get('events', [null])

    user = _events[0]['documentsource']['details']['username']

    if user is None or user == '':
        return None

    email = user + '@mozilla.com'

    return AlertTriageRequest(
        alert['_id'],
        AlertLabel.SENSITIVE_HOST_SESSION,
        _source.get('summary', 'SSH access to a sensitive host'),
        email)


def _make_duo_code_gen(alert: Alert) -> Optional[AlertTriageRequest]:
    _source = alert.get('_source', {})

    return AlertTriageRequest(
        alert['_id'],
        AlertLabel.DUO_BYPASS_CODES_GENERATED,
        _source.get('summary', 'Duo bypass codes generated'),
        '')


def _make_duo_code_used(alert: Alert) -> Optional[AlertTriageRequest]:
    _source = alert.get('_source', {})

    return AlertTriageRequest(
        alert['_id'],
        AlertLabel.DUO_BYPASS_CODES_USED,
        _source.get('summary', 'Duo bypass code used to log in'),
        '')


def _make_ssh_access_releng(alert: Alert) -> Optional[AlertTriageRequest]:
    _source = alert.get('_source', {})

    return AlertTriageRequest(
        alert['_id'],
        AlertLabel.SSH_ACCESS_SIGN_RELENG,
        _source.get('summary', 'SSH access to a RelEng signing host'),
        '')
