# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# Copyright (c) 2014 Mozilla Corporation


class message(object):
    def __init__(self):
        '''
        registers based on all values and throws an exception
        we run earlier than everyone else to verify things don't break
        '''
        self.registration = ['*']
        self.priority = 12

    def onMessage(self, message, metadata):
        raise Exception('Error in the plugin')
