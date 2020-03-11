# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# Copyright (c) 2014 Mozilla Corporation

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

        return (message, metadata)
