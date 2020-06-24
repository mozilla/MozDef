# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# Copyright (c) 2014 Mozilla Corporation


class message(object):
    def __init__(self):
        self.registration = ['githubeventsqs']
        self.priority = 20
        self.MAX_STRING_LENGTH = 3000

    def onMessage(self, message, metadata):
        if 'details' in message:
            if 'message' in message['details']:
                if type(message['details']['message']) is str \
                        and len(message['details']['message']) > self.MAX_STRING_LENGTH:
                    message['details']['message'] = message['details']['message'][:self.MAX_STRING_LENGTH]
                    message['details']['message'] += ' ...'

            if 'cmdline' in message['details']:
                if type(message['details']['cmdline']) is str \
                        and len(message['details']['cmdline']) > self.MAX_STRING_LENGTH:
                    message['details']['cmdline'] = message['details']['cmdline'][:self.MAX_STRING_LENGTH]
                    message['details']['cmdline'] += ' ...'

            if 'pr_body' in message['details']:
                if type(message['details']['pr_body']) is str \
                        and len(message['details']['pr_body']) > self.MAX_STRING_LENGTH:
                    message['details']['pr_body'] = message['details']['pr_body'][:self.MAX_STRING_LENGTH]
                    message['details']['pr_body'] += ' ...'

        if 'summary' in message:
            if type(message['summary']) is str \
                    and len(message['summary']) > self.MAX_STRING_LENGTH:
                message['summary'] = message['summary'][:self.MAX_STRING_LENGTH]
                message['summary'] += ' ...'

        return (message, metadata)
