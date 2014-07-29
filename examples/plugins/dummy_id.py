# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
# Copyright (c) 2014 Mozilla Corporation
#
# Contributors:
# Anthony Verez averez@mozilla.com


class message(object):
    def __init__(self):
        '''
        register our criteria for being passed a message
        '''

        # this plugin
        # sets a static document ID
        # for a particular event to allow you to have an event that just updates
        # current status
        self.registration = ['keyOrValueYouAlwaysWantToHaveRecentData']
        self.priority = 5

    def onMessage(self, message, metadata):
        metadata['id'] = 'f71dbe52628a3f83a77ab494817525c6'

        return (message, metadata)
