# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# Copyright (c) 2014 Mozilla Corporation

import enum
import json
import os
import typing as types

import boto3
import requests


_CONFIG_FILE = os.path.join(os.path.dirname(__file__), 'triage_bot_sqs.json')


class RESTConfig(types.NamedTuple):
    '''Configuration parameters required to talk to the MozDef REST API.
    '''

    url: str
    token: types.Optional[str]


class UserResponse(enum.Enum):
    '''Enumerates the responses a user can provide to an inquiry about an
    alert.  Here,
        * YES indicates that the user did expect some action they took to have
        triggered the alert they were notified of.
        * NO indicates that the user is not aware of any action taken by them
        that would have triggered the alert.
        * WRONG_USER indicates that the user believes they were mistakenly
        contacted.  Something is wrong on our side.
    '''

    YES = 'yes'
    NO = 'no'
    WRONG_USER = 'wrongUser'


class AlertStatus(enum.Enum):
    '''Enumerates the statuses that an alert can be in.
    '''

    MANUAL = 'manual'
    IN_PROGRESS = 'inProgress'
    ACKNOWLEDGED = 'acknowledged'
    ESCALATED = 'escalated'


class Confidence(enum.Enum):
    '''Enumerates levels of confidence in the successful lookup of a user
    identity.
    '''

    HIGHEST = 'highest'
    HIGH = 'high'
    MODERATE = 'moderate'
    LOW = 'low'
    LOWEST = 'lowest'


class UserInfo(types.NamedTuple):
    '''Information about the user contacted on Slack.
    '''

    email: str
    slack: str


class UserResponseMessage(types.NamedTuple):
    '''The message type sent by the web server component informing MozDef of
    a user's response to an inquiry about an alert.
    '''

    identifier: str
    user: UserInfo
    identityConfidence: Confidence
    response: UserResponse


def new_status(resp: UserResponse) -> AlertStatus:
    '''Determine the status to update to given a user's response.
    '''

    mapping = {
        UserResponse.YES: AlertStatus.ACKNOWLEDGED,
        UserResponse.NO: AlertStatus.ESCALATED,
        UserResponse.WRONG_USER: AlertStatus.MANUAL
    }

    return mapping.get(resp, AlertStatus.MANUAL)


def update_alert_status(msg: UserResponseMessage, api: RESTConfig):
    '''Invoke the MozDef REST API to update the status of an alert.
    '''

    status = new_status(msg.response)

    payload = {
        'alert': msg.identifier,
        'status': status.value,
        'user': {
            'email': msg.user.email,
            'slack': msg.user.slack
        },
        'identityConfidence': msg.identityConfidence.value,
        'response': msg.response.value
    }

    headers = {}

    if api.token is not None:
        headers['Authorization'] = 'Bearer {}'.format(api.token)

    try:
        resp = requests.post(api.url, headers=headers, json=payload)
    except:
        return False

    return resp.status_code < 300


def process(msg, meta, api_cfg):
    '''Inspect a message expected to contain a `UserResponseMessage` and invoke
    the MozDef REST API to update the status of the identified alert.
    '''

    ident = msg.get('identifier')
    user = msg.get('user', {})
    email = user.get('email')
    slack = user.get('slack')
    confidence = Confidence(msg.get('identityConfidence', 'lowest'))
    resp = UserResponse(msg.get('response', 'wrongUser'))

    if any([v is None for v in [ident, email, slack]]):
        return (None, None)

    response = UserResponseMessage(
        ident, UserInfo(email, slack), confidence, resp)

    update_succeeded = update_alert_status(response, api_cfg)

    if not update_succeeded:
        return (None, None)

    return (msg, meta)


class message:
    '''Updates the status of alerts when users respond to messages on Slack.
    '''

    def __init__(self):
        self.registration = 'triagebot'
        self.priority = 5
    
        with open(_CONFIG_FILE) as cfg_file:
            config = json.load(cfg_file)

        self.api_cfg = RESTConfig(
            config['rest_api_url'],
            config['rest_api_token']
        )


    def onMessage(self, message, metadata):
        if message['category'] == 'triagebot':
            return process(message, metadata, self.api_cfg)

        return (message, metadata)
