# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
# Copyright (c) 2014 Mozilla Corporation


class message(object):
    def __init__(self):
        '''
        takes an incoming custom endpoint message
        and sets the doc_type
        '''
    
        self.registration = ['customendpoint']
        self.priority = 2
 
    def onMessage(self, message, metadata):
        # set the doc type
        # to avoid data type conflicts with other doc types
        # (int vs string, etc)
        if 'endpoint' in message.keys() and 'customendpoint' in message.keys():
            if message['customendpoint']:
                if isinstance(message['endpoint'], str) or \
                   isinstance(message['endpoint'], unicode):
                    metadata['doc_type']= message['endpoint']
        return (message, metadata)
