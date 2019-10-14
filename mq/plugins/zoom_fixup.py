# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# Copyright (c) 2014 Mozilla Corporation

from mozdef_util.utilities.key_exists import key_exists


class message(object):
    def __init__(self):
        '''register our criteria for being passed a message
           as a list of lower case strings or values to match with an event's dictionary of keys or values
           set the priority if you have a preference for order of plugins to run. 0 goes first, 100 is assumed/default if not sent
        '''
        # get zoom event data
        self.registration = ['zoom_host']
        self.priority = 2

    def onMessage(self, message, metadata):
        # check for messages we have vetted as n/a and prevalent
        # from a sec standpoint and drop them also rewrite fields
        # to drop unecessary expansion

        # omit "topic" field
        if key_exists('details.payload.object.topic', message):
                del message['details']['payload']['object']['topic']

        # rewrite summary to be more informative
        message['summary'] = ""
        if key_exists('details.event', message):
            message['summary'] = "zoom: {0}".format(message['details']['event'])
            if key_exists('details.payload.object.participant.user_name', message):
                message['summary'] += " triggered by user {0}".format(message['details']['payload']['object']['participant']['user_name'])
            elif key_exists('details.payload.operator', message):
                message['summary'] += " triggered by user {0}".format(message['details']['payload']['operator'])

        # drop duplicated account_id field
        if key_exists('details.payload.account_id', message) and key_exists('details.payload.object.account_id', message):
            if message.get('details.payload.account_id') == message.get('details.payload.object.account_id'):
                    del message['details']['payload']['object']['account_id']

        return (message, metadata)
