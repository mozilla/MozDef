# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# Copyright (c) 2014 Mozilla Corporation


class message(object):
    def __init__(self):
        '''register our criteria for being passed a message
           as a list of lower case strings or values to match with an event's dictionary of keys or values
           set the priority if you have a preference for order of plugins to run. 0 goes first, 100 is assumed/default if not sent
        '''
        # get auditd data
        self.registration = ['zoom', 'mozdef-event-framework-zoom-dev']
        self.priority = 2

    def onMessage(self, message, metadata):
        # check for messages we have vetted as n/a and prevalent
        # from a sec standpoint and drop them

        # ganglia monitor daemon
        if 'details' in message and isinstance(message['details'], dict):
            if 'topic' in message['details']['payload']['object']:
                del message['details']['payload']['object']['topic']

        return (message, metadata)