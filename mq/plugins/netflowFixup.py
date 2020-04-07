# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# Copyright (c) 2014 Mozilla Corporation


class message(object):
    def __init__(self):
        '''
        takes an incoming message
        and sets the type field
        '''

        self.registration = ['netflow']
        self.priority = 5

    def onMessage(self, message, metadata):
        # set the type field for sub-categorical filtering
        message['type']= 'netflow'

        return (message, metadata)
