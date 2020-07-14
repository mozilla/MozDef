# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# Copyright (c) 2014 Mozilla Corporation

import typing as types

from mozdef_util.utilities.key_exists import key_exists


class message(object):
    def __init__(self):
        '''
        rewrites ldap's details.tls field and sets source
        '''

        self.registration = ['LDAP-Humanizer', 'ldap']
        self.priority = 5

    def onMessage(self, message, metadata):

        # check for category like 'ldap' and rename the tls field
        if key_exists('category', message):
            data = message.get('category')
            if data == 'ldap':
                if key_exists('details.tls', message):
                    message['details']['tls_encrypted'] = message['details']['tls']
                    del(message['details']['tls'])

        if 'source' not in message:
            message['source'] = 'ldap'

        details = message.get('details', {})
        actor_str = details.get('actor', '')
        actor_email = _parse_email_from_actor(actor_str)

        if actor_email is None:
            details['email'] = None
            details['username'] = None

            message['details'] = details

            return (message, metadata)

        username = actor_email.split('@')[0]

        details['email'] = actor_email
        details['username'] = username

        message['details'] = details

        return (message, metadata)


def _parse_email_from_actor(actor_str: str) -> types.Optional[str]:
    '''Parse the email from a string like
    `"mail=username@mozilla.com,o=com,dc=mozilla"`
    '''

    mapping = {}

    pairs = []

    for section in actor_str.split(' '):
        pairs.extend(section.split(','))

    for item in pairs:
        pair = item.split('=')

        if len(pair) == 2:
            mapping[pair[0]] = pair[1]

    return mapping.get('mail')
