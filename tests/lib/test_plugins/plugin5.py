# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
# Copyright (c) 2014 Mozilla Corporation
#
# Contributors:
# Brandon Myers bmyers@mozilla.com


class message(object):
    def __init__(self):
        '''
        modifies the metadata
        '''
        self.registration = ['grapes']
        self.priority = 25

    def onMessage(self, message, metadata):
        metadata['plugin5_key'] = 'grapes'
        return message, metadata
