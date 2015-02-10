# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
# Copyright (c) 2014 Mozilla Corporation
#
# Contributors:
# Jeff Bryner jbryner@mozilla.com

import os
import sys
from configlib import getConfig, OptionParser

class message(object):
    def __init__(self):
        '''register our criteria for being passed a message
           as a list of lower case strings to match with an rest endpoint
           (i.e. blockip matches /blockip)
           set the priority if you have a preference for order of plugins
           0 goes first, 100 is assumed/default if not sent
           
           Plugins will register in Meteor with attributes:
           name: (as below)
           description: (as below)
           priority: (as below)
           file: "plugins.filename" where filename.py is the plugin code.
           
           Plugin gets sent main rest options as:
           self.restoptions
           self.restoptions['configfile'] will be the .conf file
           used by the restapi's index.py file.
           
        '''

        self.registration = ['test',
                             'testendpoint2'
                             ]
        self.priority = 10
        self.name = "TestPlugin"
        self.description = "Just a thing to test with"
        # set my own conf file
        # relative path to the rest index.py file
        self.configfile = './plugins/test.conf'
        self.options = None
        if os.path.exists(self.configfile):
            print('found conf file {0}'.format(self.configfile))
            self.initConfiguration()
        

    def initConfiguration(self):
        myparser = OptionParser()
        # setup self.options by sending empty list [] to parse_args
        (self.options, args) = myparser.parse_args([])
        
        # fill self.options with plugin-specific options
        
        # example: set a default time zone for when it's not specified
        self.options.defaultTimeZone = getConfig('defaulttimezone', 'US/Pacific', self.configfile)

        #print(self.options)
        #print(self.options.defaultTimeZone)
        
    def onMessage(self, request, response):
        '''
        request: http://bottlepy.org/docs/dev/api.html#the-request-object
        response: http://bottlepy.org/docs/dev/api.html#the-response-object
        
        '''
        # example actions: add a header
        response.headers['X-PLUGIN'] = self.description
        
        # example actions: read data sent as json
        # print(request.json)
        
        return (request, response)
