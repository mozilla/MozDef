# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# Copyright (c) 2014 Mozilla Corporation


class message(object):

    def __init__(self):
        '''
        takes an incoming message
        and sets the keys to lowercase
        '''

        self.registration = ['cloudtrail', 'vidyo', 'suricata', 'guardduty', 'uptycs']
        self.priority = 4

    def onMessage(self, message, metadata):
        def renameKeysToLower(message):
            if isinstance(message, dict):
                message_keys = list(message.keys())
                for key in message_keys:
                    message[key.lower()] = message.pop(key)
                    if isinstance(message[key.lower()], dict) or isinstance(message[key.lower()], list):
                        message[key.lower()] = renameKeysToLower(message[key.lower()])
            elif isinstance(message, list):
                for item in message:
                    item = renameKeysToLower(item)
            return message

        message = renameKeysToLower(message)
        return (message, metadata)
