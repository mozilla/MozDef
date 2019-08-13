# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# Copyright (c) 2014 Mozilla Corporation

import requests
import json
import os
from configlib import getConfig, OptionParser

from mozdef_util.utilities.logger import logger


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

        self.registration = ['ipintel']
        self.priority = 5
        self.name = "cymon"
        self.description = "IP intel from the cymon.io api"

        # set my own conf file
        # relative path to the rest index.py file
        self.configfile = './plugins/cymon.conf'
        self.options = None
        if os.path.exists(self.configfile):
            logger.debug('found conf file {0}\n'.format(self.configfile))
            self.initConfiguration()

    def onMessage(self, request, response):
        '''
        request: http://bottlepy.org/docs/dev/api.html#the-request-object
        response: http://bottlepy.org/docs/dev/api.html#the-response-object

        '''
        if request.body:
            arequest = request.body.read()
            request.body.close()
        try:
            requestDict = json.loads(arequest)
        except ValueError:
            response.status = 500

        if 'ipaddress' in requestDict:
            url = "https://cymon.io/api/nexus/v1/ip/{0}/events?combined=true&format=json".format(requestDict['ipaddress'])

            # add the cymon api key?
            if self.options is not None:
                headers = {'Authorization': 'Token {0}'.format(self.options.cymonapikey)}

            else:
                headers = None

            dresponse = requests.get(url, headers=headers)
            if dresponse.status_code == 200:
                response.content_type = "application/json"
                response.body = dresponse.content
                response.status = 200
            else:
                response.status = dresponse.status_code

        else:
            response.status = 500

        return (request, response)

    def initConfiguration(self):
        myparser = OptionParser()
        # setup self.options by sending empty list [] to parse_args
        (self.options, args) = myparser.parse_args([])

        # fill self.options with plugin-specific options

        # cymon options
        self.options.cymonapikey = getConfig('cymonapikey',
                                             '',
                                             self.configfile)
