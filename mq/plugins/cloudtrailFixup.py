# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
# Copyright (c) 2014 Mozilla Corporation
#
# Contributors:
# Brandon Myers bmyers@mozilla.com


class message(object):
    def __init__(self):
        '''register our criteria for being passed a message
           as a list of lower case strings or values to match with an event's dictionary of keys or values
           set the priority if you have a preference for order of plugins to run. 0 goes first, 100 is assumed/default if not sent
        '''
        # get auditd data
        self.registration = ['cloudtrail']
        self.priority = 2

    def onMessage(self, message, metadata):
        # Convert apiVersion with the format '2016_01_02'
        # to '2016-01-02'
        # This is a result of apiVersion mapping being a dateOptionalTime
        # https://bugzilla.mozilla.org/show_bug.cgi?id=1313780
        if 'apiVersion' in message.keys():
            message['apiVersion'] = message['apiVersion'].replace('_', '-')

        return (message, metadata)
