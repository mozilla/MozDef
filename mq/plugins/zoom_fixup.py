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
        # get zoom event data
        self.registration = ['zoom']
        self.priority = 2

    def onMessage(self, message, metadata):
        # check for messages we have vetted as n/a and prevalent
        # from a sec standpoint and drop them also rewrite fields
        # to drop unecessary expansion

        # omit "topic" field
        if 'details' in message and isinstance(message['details'], dict):
            if 'topic' in message['details']['payload']['object']:
                del message['details']['payload']['object']['topic']
            # rewrite summary to be more informative
            if 'event' in message['details'] and 'user_name' in message['details']['payload']['object']['participant']:
                message['summary'] = message['details']['event']
                temp = " triggered by user "
                temp2 = message['details']['payload']['object']['participant']['user_name']
                message['summary'] += temp
                message['summary'] += temp2
                del temp
                del temp2
            # drop duplicated account_id field
            if 'payload' in message['details'] and isinstance(message['details']['payload'], dict):
                if 'account_id' in message['details']['payload'] and 'account_id' in message['details']['payload']['object']:
                    if message.get('details.payload.account_id') == message.get('details.payload.object.account_id'):
                        del message['details']['payload']['object']['account_id'] 

        return (message, metadata)
