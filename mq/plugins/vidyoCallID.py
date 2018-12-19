# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
# Copyright (c) 2014 Mozilla Corporation

import hashlib


class message(object):
    def __init__(self):
        '''
        takes an incoming vidyo call record and assigns a static ID
        so we always update the same doc for current status.
        '''

        # this plugin
        # sets a static document ID
        # for a particular event to allow you to have an event that just updates
        # current status
        self.registration = ['uniquecallid']
        self.priority = 5

    def onMessage(self, message, metadata):
        docid = hashlib.md5('vidyouniquecallid' + message['details']['uniquecallid']).hexdigest()
        metadata['id'] = docid
        metadata['doc_type'] = 'vidyo'
        return (message, metadata)
