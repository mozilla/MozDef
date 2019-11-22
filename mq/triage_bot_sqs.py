# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# Copyright (c) 2014 Mozilla Corporation

import enum
import json
import os
import typing as types

from mozdef_util.utilities.logger import logger

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
        resp = requests.post(url, headers=headers, data=payload)
    except:
        logger.exception('Failed to send request to MozDef REST API')
        return

    if resp.status_code >= 300:
        logger.error('Update of alert {} status failed'.format(alert_id))


def process(msg, api_cfg):
    '''Inspect a message expected to contain a `UserResponseMessage` and invoke
    the MozDef REST API to update the status of the identified alert.
    '''

    try:
        response = UserResponseMessage(**json.loads(msg.body))
    except:
        logger.error('Invalid message format{}'.format(msg.body))
        return

    status = new_status(response.response)

    update_alert_status(response.identifier, status, api_cfg)


def main():
    with open(_CONFIG_FILE) as cfg_file:
        config = json.load(cfg_file)

    aws_creds = {
        'aws_access_key_id': config['aws_access_key_id'],
        'aws_secret_access_key': config['aws_secret_access_key']
    }

    api_cfg = RESTConfig(config['rest_api_url'], config['rest_api_token'])

    sqs = boto3.resource('sqs', region=config['aws_region'], **aws_creds)

    queue = sqs.get_queue_by_name(QueueName=config['sqs_queue_name'])

    while True:
        try:
            messages = queue.receive_messages(
                MaxNumberOfMessages=cfg['sqs_message_bulk_size']
            )
            for message in messages:
                process(message, api_cfg)
        except KeyboardInterrupt:
            logger.info('Exiting triage_bot_sqs worker')
        except Exception as e:
            logger.exception('Error in triage_bot_sqs: {}'.format(e.message))


if __name__ == '__main__':
    main()
