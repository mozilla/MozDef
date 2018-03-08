# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
# Copyright (c) 2014 Mozilla Corporation


class message(object):
    def __init__(self):
        '''
        takes an incoming message
        and removes quotes from etag field
        '''

        self.registration = ['google']
        self.priority = 5

    def onMessage(self, message, metadata):
        # make sure it's a google activity event
        # and do any clean up

        # check for details.kind like 'admin#reports#activity'
        if ( 'details' in message.keys() and
             'kind' in message['details'].keys() and
             'activity' in message['details']['kind']):

            # details.etag might be quoted..unquote it
            if 'etag' in message['details'].keys():
                message['details']['etag'] = message['details']['etag'].replace('"', '')

        return (message, metadata)
