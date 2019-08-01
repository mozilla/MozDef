# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# Copyright (c) 2014 Mozilla Corporation


class message(object):
    def __init__(self):
        '''
        intended to be the fourth plugin that will run
        and signals to delete the message (returning None)
        '''
        self.registration = ['pears']
        self.priority = 20

    def onMessage(self, message, metadata):
        return None, metadata
