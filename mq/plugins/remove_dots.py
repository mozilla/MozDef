# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# Copyright (c) 2014 Mozilla Corporation


class message(object):

    def __init__(self):
        '''
        takes an incoming message and checks for dots at the
        start or end of the key and removes them
        '''

        self.registration = ['cloudtrail']
        self.priority = 5

    def onMessage(self, message, metadata):
        def renameKeysToRemoveDots(message):
            if isinstance(message, dict):
                message_keys = list(message.keys())
                for key in message_keys:
                    if len(key) > 0 and (key[0] == '.' or key[-1] == '.'):
                        new_key = key.replace(".", "")
                        if new_key != key:
                            message[new_key] = message.pop(key)
                    if isinstance(message.get(key), (dict, list)):
                        message[key] = renameKeysToRemoveDots(message[key])
            elif isinstance(message, list):
                for item in message:
                    item = renameKeysToRemoveDots(item)
            return message

        message = renameKeysToRemoveDots(message)
        return (message, metadata)
