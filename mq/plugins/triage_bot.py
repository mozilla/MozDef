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
    token: str


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


class UserResponseMessage(types.NamedTuple):
    '''The message type sent by the web server component informing MozDef of
    a user's response to an inquiry about an alert.
    '''

    identifier: str
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


def update_alert_status(alert_id: str, status: AlertStatus, api: RESTConfig):
    '''Invoke the MozDef REST API to update the status of an alert.
    '''

    payload = {
        'alert': alert_id,
        'status': status.value
    }

    headers = {
        'Authorization': 'Bearer {}'.format(api.token)
    }

    try:
        resp = requests.post(api.url, headers=headers, data=payload)
    except:
        return False

    return resp.status_code < 300


def process(msg, meta, api_cfg):
    '''Inspect a message expected to contain a `UserResponseMessage` and invoke
    the MozDef REST API to update the status of the identified alert.
    '''

    try:
        ident = msg['identifier']
        resp = UserResponse(msg['response'])
        response = UserResponseMessage(ident, resp)
    except:
        return (None, None)

    status = new_status(response.response)

    update_succeeded = update_alert_status(response.identifier, status, api_cfg)

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
