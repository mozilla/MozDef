# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
# Copyright (c) 2014 Mozilla Corporation
#
# Contributors:
# Jeff Bryner jbryner@mozilla.com

import requests
import json


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
        except ValueError as e:
            response.status = 500


        print(requestDict, requestDict.keys())
        if 'ipaddress' in requestDict.keys():
            url="https://cymon.io/api/public/nexus?ip="

            dresponse = requests.get('{0}{1}&format=json'.format(url, requestDict['ipaddress']))
            if dresponse.status_code == 200:
                response.content_type = "application/json"
                response.body = dresponse.content
            else:
                response.status = dresponse.status_code

        else:
            response.status = 500

        return (request, response)