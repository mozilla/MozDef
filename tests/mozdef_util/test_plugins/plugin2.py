# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# Copyright (c) 2014 Mozilla Corporation


class message(object):
    def __init__(self):
        '''
        intended to be the second plugin that will run
        and adds a term to the message to signal
        it has run and has overwrote the key
        '''
        self.registration = 'bananas'
        self.priority = 10

    def onMessage(self, message, metadata):
        message['unit_test_key'] = 'bananas'
        return message, metadata
