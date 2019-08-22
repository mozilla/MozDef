# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# Copyright (c) 2017 Mozilla Corporation


class message(object):
    def __init__(self):
        '''
            Plugin used to fix object type discretions with cloudtrail messages
        '''
        self.registration = ['cloudtrail']
        self.priority = 10

        # The following keys will get moved from details.<key>
        # to details.<aws_service>.<key>
        self.modify_keys = [
            'additionaleventdata',
            'serviceeventdetails',
            'requestparameters',
            'responseelements',
            'apiversion'
        ]

    def onMessage(self, message, metadata):
        if 'source' not in message:
            return (message, metadata)

        if 'hostname' not in message:
            return (message, metadata)

        if 'details' not in message:
            return (message, metadata)

        if not message['source'] == 'cloudtrail':
            return (message, metadata)

        service = message['hostname']
        for modified_key in self.modify_keys:
            if modified_key in message['details']:
                # Move to details.<service>.<modified_key
                if service not in message['details']:
                    message['details'][service] = {}
                message['details'][service][modified_key] = message['details'][modified_key]
                del message['details'][modified_key]

        return (message, metadata)
