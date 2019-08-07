# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# Copyright (c) 2014 Mozilla Corporation


class message(object):
    def __init__(self):
        '''
        intended to be the third plugin that will run
        and adds a term to the message to signal
        it has run
        '''
        self.registration = ['oranges']
        self.priority = 15

    def onMessage(self, message, metadata):
        message['plugin3_key'] = 'oranges'
        return message, metadata
