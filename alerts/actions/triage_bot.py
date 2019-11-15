# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# Copyright (c) 2014 Mozilla Corporation

from datetime import datetime
from enum import Enum
import json
import os
import typing as types
from urllib.parse import urljoin

import boto3
import requests


CONFIG_FILE = os.path.join(os.path.dirname(__file__), 'triage_bot.json')

Alert = types.Dict[types.Any, types.Any]
Email = str


class AlertLabel(Enum):
    '''Enumerates each of the alerts supported by the triage bot.
    '''

    SENSITIVE_HOST_SESSION = 'sensitive_host_session'
    DUO_BYPASS_CODES_USED = 'duo_bypass_codes_used'
    DUO_BYPASS_CODES_GENERATED = 'duo_bypass_codes_generated'
    SSH_ACCESS_SIGN_RELENG = 'ssh_access_sign_releng'

# TODO: Change to a dataclass when Python 3.7+ is adopted.

class AlertTriageRequest(types.NamedTuple):
    '''A message bound for the AWS lambda function that interfaces with Slack.
    '''

    identifier: str
    alert: AlertLabel
    summary: str
    user: Email


class AuthParams(types.NamedTuple):
    '''Configuration parameters required to authenticate using OAuth in order
    to retrieve credentials used to further authenticate to the Person API.
    '''

    client_id: str
    client_secret: str
    audience: str
    scope: str
    grants: str


class User(types.NamedTuple):
    '''A container for information describing a user profile that is not
    security critical.
    '''

    created: datetime
    first_name: str
    last_name: str
    alternative_name: str
    primary_email: str
    mozilla_ldap_primary_email: str


class DispatchResult(Enum):
    '''A ternary good / bad / unknown result type indicating whether a dispatch
    to AWS Lambda was successful.
    '''

    SUCCESS = 'success'
    FAILURE = 'failure'
    INDETERMINATE = 'indeterminate'


# We define some types to serve as 'interfaces' that can be referenced for
# higher level functions and testing purposes.
# This module defines implementations of each interface.

Url = str
Token = str
Username = str
AuthInterface = types.Callable[[Url, AuthParams], types.Optional[Token]]
UserByNameInterface = types.Callable[
    [Url, Token, Username],
    types.Optional[User]]
DispatchInterface = types.Callable[[AlertTriageRequest, str], DispatchResult]

class message(object):
    '''The main interface to the alert action.
    '''

    def __init__(self):
        '''Loads the configuration for the action and announces which alerts
        the action can be run against.
        '''

        with open(CONFIG_FILE) as cfg_file:
            self._config = json.load(cfg_file)

        self._boto_session = boto3.session.Session(
            region_name=self._config['aws_region'],
            aws_access_key_id=self._config['aws_access_key_id'],
            aws_secret_access_key=self._config['aws_secret_access_key']
        )

        self.registration = '*'
        self.priority = 1


    def onMessage(self, message):
        '''The main entrypoint to the alert action invoked with a message
        describing an alert.
        '''

        request = try_make_outbound(message)

        dispatch = _dispatcher(self._boto_session)

        if request is not None:
            self._test_flag = True
            print(request)

        return message


def try_make_outbound(message: Alert) -> types.Optional[AlertTriageRequest]:
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


def authenticate(url: Url, params: AuthParams) -> types.Optional[Token]:
    '''An `AuthInterface` that uses the `requests` library to make a POST
    request to the Person API containing the required credentials formatted as
    JSON.
    '''

    payload = {
        'client_id': params.client_id,
        'client_secret': params.client_secret,
        'audience': params.audience,
        'scope': params.scope,
        'grant_type': params.grants
    }

    try:
        resp = requests.post(url, json=payload)
        return resp.json().get('access_token')
    except:
        return None


def primary_username(
    base: Url,
    tkn: Token,
    uname: Username
    ) -> types.Optional[User]:
    '''An `UserByNameInterface` that uses the `requests` library to make a GET
    request to the Person API in order to fetch a user profile given that
    user's primary username.

    The `base` argument is the base URL for the Person API such as
    `https://person.api.com`.  This function will invoke the appropriate route.

    `tkn` must be an authenticated session token produced by an `AuthInterface`.

    `uname` is the string username of the user whose account to retrieve.
    '''

    route = '/v2/user/primary_username/{}'.format(uname)
    full_url = urljoin(base, route)

    headers = {
        'Authorization': 'Bearer {}'.format(tkn)
    }

    try:
        resp = requests.get(full_url, headers=headers)
    except requests.exceptions.RequestException:
        return None

    data = resp.json()

    try:
        created = datetime.strptime(
            data.get('created', {}).get('value', ''),
            '%Y-%m-%dT%H:%M:%S.%fZ')
    except ValueError:
        return None

    ldap_email = data['identities']['mozilla_ldap_primary_email'].get('value')
    if ldap_email is None:
        return None

    return User(
        created=created,
        first_name=data['first_name'].get('value', 'N/A'),
        last_name=data['last_name'].get('value', 'N/A'),
        alternative_name=data['alternative_name'].get('value', 'N/A'),
        primary_email=data['primary_email'].get('value', 'N/A'),
        mozilla_ldap_primary_email=ldap_email)


def _dispatcher(boto_session) -> DispatchInterface:
    lambda_ = boto_session.client('lambda')

    def dispatch(req: AlertTriageRequest, fn_name: str) -> DispatchResult:
        # Enum variants are not directly JSON-serializable and converting Thing.B
        # to a string produces 'Thing.B'.  We just want the variant name, in
        # lowercase 'b' in this case, so we pull it out here.
        payload_dict = dict(req._asdict())
        payload_dict['alert'] = str(payload_dict['alert'])
        dot_ind = payload_dict['alert'].index('.')
        payload_dict['alert'] = payload_dict['alert'][dot_ind + 1:].lower()

        payload = bytes(json.dumps(payload_dict), 'utf-8')

        status = 200

        try:
            resp = lambda_.invoke(FunctionName=fn_name, Payload=payload)
            status = resp.get('StatusCode', 400)
        except:
            status = 500

        if status >= 400:
            return DispatchResult.FAILURE
        elif status < 300:
            return DispatchResult.SUCCESS

        return DispatchResult.INDETERMINATE

    return dispatch

def _make_sensitive_host_access(a: Alert) -> types.Optional[AlertTriageRequest]:
    null = {
        'documentsource': {
            'details': {
                'username': None
            }
        }
    }

    _source = a.get('_source', {})
    _events = _source.get('events', [null])

    user = _events[0]['documentsource']['details']['username']

    if user is None or user == '':
        return None

    email = user + '@mozilla.com'

    return AlertTriageRequest(
        a['_id'],
        AlertLabel.SENSITIVE_HOST_SESSION,
        _source.get('summary', 'SSH access to a sensitive host'),
        email)


def _make_duo_code_gen(alert: Alert) -> types.Optional[AlertTriageRequest]:
    _source = alert.get('_source', {})

    return AlertTriageRequest(
        alert['_id'],
        AlertLabel.DUO_BYPASS_CODES_GENERATED,
        _source.get('summary', 'Duo bypass codes generated'),
        '')


def _make_duo_code_used(alert: Alert) -> types.Optional[AlertTriageRequest]:
    _source = alert.get('_source', {})

    return AlertTriageRequest(
        alert['_id'],
        AlertLabel.DUO_BYPASS_CODES_USED,
        _source.get('summary', 'Duo bypass code used to log in'),
        '')


def _make_ssh_access_releng(alert: Alert) -> types.Optional[AlertTriageRequest]:
    _source = alert.get('_source', {})

    return AlertTriageRequest(
        alert['_id'],
        AlertLabel.SSH_ACCESS_SIGN_RELENG,
        _source.get('summary', 'SSH access to a RelEng signing host'),
        '')
