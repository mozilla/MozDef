# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# Copyright (c) 2014 Mozilla Corporation

import json


class message(object):

    def __init__(self):
        '''
        takes an incoming message
        and checks for dots at the
        start or end of the key and
        removes them
        '''

        self.registration = ['cloudtrail']
        self.priority = 5

    def onMessage(self, message, metadata):
        def remove_dots(obj):
            for key in obj.keys():
                if key[0] == '.' or key[-1] == '.':
                    new_key = key.replace(".","")
                    if new_key != key:
                        obj[new_key] = obj[key]
                        del obj[key]
            return obj

        new_json = json.loads(json.dumps(message), object_hook=remove_dots)
        message = new_json

        return (message, metadata)
