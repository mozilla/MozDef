# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# Copyright (c) 2014 Mozilla Corporation


class message(object):
    def __init__(self):
        '''register our criteria for being passed a message
           return a dict with fieldname:None to be sent anything with that field
           return a dict with fieldname:Value to be sent anything with that field/value
           return a string to be sent anything with any field matching that string evaluated as a regex.
           set the priority if you have a preference for order of plugins to run.
           0 goes first, 100 is assumed/default if not sent
        '''

        # this plugin inspects messages for whitelist stuff that
        # should be dropped and not processed any further.
        self.registration = ['ELB-HealthChecker/1.0']
        self.priority = 1

    def onMessage(self, message, metadata):
        # criteria for dropping messages
        # early exit by setting message = None and return
        if 'type' in message and message['type'] != 'auditd':
            return (message, metadata)

        if 'details' in message:
            # drop disabled for now
            # if 'signatureid' in message['details']:
                # if message['details'].lower() == 'execve' and \
                    # 'command' not in message['details']:
                    # auditd entry without a command
                    # likely a result of another command (java starting a job, etc.)
                    # signal a drop

                    # message = None
                    # return message
            if 'http_user_agent' in message['details']:
                if message['details']['http_user_agent'] == 'ELB-HealthChecker/1.0':
                    message = None
                    return message

        return (message, metadata)
