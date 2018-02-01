# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
# Copyright (c) 2017 Mozilla Corporation


class message(object):
    def __init__(self):
        '''
            Plugin used to fix object type discretions with cloudtrail messages
        '''
        self.registration = ['cloudtrail']
        self.priority = 10

    def onMessage(self, message, metadata):
        if 'source' not in message:
            return (message, metadata)

        if not message['source'] == 'cloudtrail':
            return (message, metadata)

        if 'details' not in message:
            return (message, metadata)

        if 'requestparameters' not in message['details']:
            return (message, metadata)

        if type(message['details']['requestparameters']) is not dict:
            return (message, metadata)

        # Handle iamInstanceProfile strings
        if 'iamInstanceProfile' in message['details']['requestparameters']:
            iam_instance_profile = message['details']['requestparameters']['iamInstanceProfile']
            if type(iam_instance_profile) is not dict:
                message['details']['requestparameters']['iamInstanceProfile'] = {
                    'raw_value': iam_instance_profile
                }

        # Handle attribute strings
        if 'attribute' in message['details']['requestparameters']:
            attribute = message['details']['requestparameters']['attribute']
            if type(attribute) is not dict:
                message['details']['requestparameters']['attribute'] = {
                    'raw_value': attribute
                }

        return (message, metadata)
