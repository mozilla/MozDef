# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# Copyright (c) 2014 Mozilla Corporation


class message(object):
    def __init__(self):
        '''register our criteria for being passed a message
           as a list of lower case strings or values to match with an event's dictionary of keys or values
           set the priority if you have a preference for order of plugins to run.
           0 goes first, 100 is assumed/default if not sent
        '''
        self.registration = ['user_feedback']
        self.priority = 20

    def onMessage(self, message, metadata):
        if 'details' in message and type(message['details']) == dict:
            if 'alert_information' in message['details'] and type(message['details']['alert_information']) == dict:
                if 'summary' in message['details']['alert_information']:
                    message['summary'] = message['details']['alert_information']['summary']
        return (message, metadata)
