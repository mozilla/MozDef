# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# Copyright (c) 2014 Mozilla Corporation


class message(object):
    def __init__(self):
        '''
        registers based on all values
        '''
        self.registration = ['*']
        self.priority = 35

    def onMessage(self, message, metadata):
        message['plugin7_key'] = 'lime'
        return message, metadata
