# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
# Copyright (c) 2014 Mozilla Corporation
#
# Contributors:
# Jeff Bryner jbryner@mozilla.com

class message(object):
    def __init__(self):
        '''register our criteria for being passed a message
           as a list of lower case strings to match with an rest endpoint (i.e. blockip matches /blockip)
           set the priority if you have a preference for order of plugins to run. 0 goes first, 100 is assumed/default if not sent
        '''

        self.registration = ['test',
                             'kibanadashboards'
                             ]
        self.priority = 10
        self.name = "TestPlugin"
        self.description = "Just something to test with"
        
    def onMessage(self, request, response):
        response.headers['X-PLUGIN'] = self.description
        print(request, response)
        return (request, response)
