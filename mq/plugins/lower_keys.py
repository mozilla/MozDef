# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
# Copyright (c) 2014 Mozilla Corporation


class message(object):

    def __init__(self):
        '''
        takes an incoming message
        and sets the keys to lowercase
        '''

        self.registration = ['summary']
        self.priority = 5

    def onMessage(self, message, metadata):
        if isinstance(message, dict):
            message = dict((k.lower(), v) for k, v in message.items())
            return (message, metadata)
