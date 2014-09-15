# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
# Copyright (c) 2014 Mozilla Corporation
#
# Contributors:
# Jeff Bryner jbryner@mozilla.com


class message(object):
    def __init__(self):
        '''
        takes an incoming message
        and sets the doc_type
        '''
    
        self.registration = ['netflow']
        self.priority = 5
 
    def onMessage(self, message, metadata):
        # set the doc type
        # to avoid data type conflicts with other doc types 
        # (int v string, etc)
        metadata['doc_type']= 'netflow'

        return (message, metadata) 