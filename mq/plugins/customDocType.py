# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# Copyright (c) 2014 Mozilla Corporation


class message(object):
    def __init__(self):
        '''
        takes an incoming custom endpoint message
        and sets the type sub-category filter
        '''

        self.registration = ['customendpoint']
        self.priority = 2

    def onMessage(self, message, metadata):
        # set the type field for sub-categorical filtering
        if 'endpoint' in message and 'customendpoint' in message:
            if message['customendpoint']:
                if isinstance(message['endpoint'], str):
                    message['type'] = message['endpoint']
        return (message, metadata)
