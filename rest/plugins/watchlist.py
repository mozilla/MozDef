# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# Copyright (c) 2014 Mozilla Corporation

import os
import random
from configlib import getConfig, OptionParser
from datetime import datetime, timedelta
from pymongo import MongoClient

from mozdef_util.utilities.logger import logger


def genMeteorID():
    return('%024x' % random.randrange(16**24))


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

        self.registration = ['watchitem']
        self.priority = 10
        self.name = "WatchList"
        self.description = "Watch List"

        # set my own conf file
        # relative path to the rest index.py file
        self.configfile = './plugins/watchlist.conf'
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

    def watchItem(self,
                  watchcontent=None,
                  comment=None,
                  duration=None,
                  referenceID=None,
                  userID=None):
        try:
            # DB connection/table
            mongoclient = MongoClient(self.options.mongohost, self.options.mongoport)
            watchlist = mongoclient.meteor['watchlist']

            # already in the table?
            watched = watchlist.find_one({'watchcontent': str(watchcontent)})
            if watched is None:
                # insert
                watched=dict()
                watched['_id']=genMeteorID()
                watched['watchcontent']=str(watchcontent)
                watched['dateAdded']=datetime.utcnow()
                # Compute start and end dates
                # default
                end_date = datetime.utcnow() + timedelta(hours=1)
                if duration == '12hr':
                    end_date = datetime.utcnow() + timedelta(hours=12)
                elif duration == '1d':
                    end_date = datetime.utcnow() + timedelta(days=1)
                elif duration == '2d':
                    end_date = datetime.utcnow() + timedelta(days=2)
                elif duration == '3d':
                    end_date = datetime.utcnow() + timedelta(days=3)
                elif duration == '1w':
                    end_date = datetime.utcnow() + timedelta(days=7)
                elif duration == '30d':
                    end_date = datetime.utcnow() + timedelta(days=30)
                watched['dateExpiring']=end_date
                watched['comment']=comment
                watched['creator']=userID
                watched['reference']=referenceID
                ref=watchlist.insert(watched)
                logger.debug('{0} written to db.\n'.format(ref))
                logger.debug('%s added to the watchlist table.\n' % (watchcontent))

            else:
                logger.error('%s is already present in the watchlist table\n' % (str(watchcontent)))
        except Exception as e:
            logger.error('Error while watching %s: %s\n' % (watchcontent, e))

    def onMessage(self, request, response):
        '''
        request: http://bottlepy.org/docs/dev/api.html#the-request-object
        response: http://bottlepy.org/docs/dev/api.html#the-response-object
        '''
        response.headers['X-PLUGIN'] = self.description

        watchcontent = None
        comment = None
        duration = None
        referenceID = None
        userid = None
        watchitem = False

        # loop through the fields of the form
        # and fill in our values
        try:
            for field in request.json:
                if self.name in field:
                    watchitem = field[self.name]
                if 'watchcontent' in field:
                    watchcontent = field['watchcontent']
                if 'duration' in field:
                    duration = field['duration']
                if 'comment' in field:
                    comment = field['comment']
                if 'referenceid' in field:
                    referenceID = field['referenceid']
                if 'userid' in field:
                    userid = field['userid']
            if watchitem and watchcontent is not None:
                if len(watchcontent) < 2:
                    logger.error('{0} does not meet requirements. Not added. \n'.format(watchcontent))

                else:
                    self.watchItem(str(watchcontent),
                                   comment,
                                   duration,
                                   referenceID,
                                   userid)

        except Exception as e:
            logger.error('Error handling request.json %r \n' % (e))

        return (request, response)
