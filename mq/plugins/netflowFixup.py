# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
# Copyright (c) 2014 Mozilla Corporation
#
# Contributors:
# Anthony Verez averez@mozilla.com

class message(object):
    def __init__(self):
        '''register our criteria for being passed a message
           as a list of lower case strings or values to match with an event's dictionary of keys or values
           set the priority if you have a preference for order of plugins to run. 0 goes first, 100 is assumed/default if not sent
        '''
        self.registration = ['network,netflow']
        self.priority = 10

    def onMessage(self, message, metadata):

        fields = ['tags', 'summary', 'category', 'severity']

        if 'details' in message.keys():
            # details.something -> something
            for field in fields:
                if field in message['details'].keys():
                    message[field] = message['details'][field]
                    del message['details'][field]

        return (message, metadata)

