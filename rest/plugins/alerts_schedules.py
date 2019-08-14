# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# Copyright (c) 2014 Mozilla Corporation

import os
import json
from configlib import getConfig, OptionParser
from pymongo import MongoClient

from mozdef_util.utilities.logger import logger


class message(object):
    def __init__(self):
        '''register our criteria for being passed a message
           as a list of lower case strings to match with an rest endpoint
           (i.e. watchitem matches /watchitem)
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

        self.registration = ['alertsschedules']
        self.priority = 10
        self.name = "AlertsSchedules"
        self.description = "Information on alerts schedules"

        self.configfile = './plugins/alerts_schedules.conf'
        self.options = None
        if os.path.exists(self.configfile):
            logger.debug('found conf file {0}\n'.format(self.configfile))
        self.initConfiguration()

    def initConfiguration(self):
        myparser = OptionParser()
        # setup self.options by sending empty list [] to parse_args
        (self.options, args) = myparser.parse_args([])

        # fill self.options with plugin-specific options
        self.options.mongohost = getConfig(
            'mongohost',
            'localhost',
            self.configfile)
        self.options.mongoport = getConfig(
            'mongoport',
            3001,
            self.configfile)

    def onMessage(self, request, response):
        '''
        request: http://bottlepy.org/docs/dev/api.html#the-request-object
        response: http://bottlepy.org/docs/dev/api.html#the-response-object
        '''
        mongoclient = MongoClient(self.options.mongohost, self.options.mongoport)
        schedulers_db = mongoclient.meteor['alerts_schedules']

        mongodb_alerts = schedulers_db.find()
        # logger.info("**** Current Alert Schedule ****")
        alerts_schedules_dict = {}
        for mongodb_alert in mongodb_alerts:
            alerts_schedules_dict[mongodb_alert['name']] = {
                '_id': str(mongodb_alert['_id']),
                'enabled': mongodb_alert['enabled'],
                'last_run_at': mongodb_alert['last_run_at'].isoformat(),
                'run_immediately': mongodb_alert['run_immediately'],
            }
            if 'crontab' in mongodb_alert:
                alerts_schedules_dict[mongodb_alert['name']]['schedule_type'] = 'crontab'
                alerts_schedules_dict[mongodb_alert['name']]['crontab'] = mongodb_alert['crontab']
            elif 'interval' in mongodb_alert:
                alerts_schedules_dict[mongodb_alert['name']]['schedule_type'] = 'interval'
                alerts_schedules_dict[mongodb_alert['name']]['interval'] = mongodb_alert['interval']

        response.body = json.dumps(alerts_schedules_dict)
        response.status = 200

        return (request, response)
