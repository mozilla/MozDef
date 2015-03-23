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
        takes an incoming alert
        and simply prints it
        '''
    
        self.registration = ['bro']
        self.priority = 2
 
    def onMessage(self, message):
        # here is where you do something with the incoming alert message
        if 'summary' in message.keys() :
            print message['summary']
        
        # you can modify the message if needed
        # plugins registered with lower (>2) priority
        # will receive the message and can also act on it
        # but even if not modified, you must return it
        return message