# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
# Copyright (c) 2014 Mozilla Corporation

import os
import random
import requests
import re
import sys
from configlib import getConfig, OptionParser
from datetime import datetime, timedelta
from pymongo import MongoClient


def isFQDN(fqdn):
    try:
        # We could resolve FQDNs here, but that could tip our hand and it's
        # possible us investigating could trigger other alerts.
        # validate using the regex from https://github.com/yolothreat/utilitybelt
        fqdn_re = re.compile('(?=^.{4,255}$)(^((?!-)[a-zA-Z0-9-]{1,63}(?<!-)\.)+[a-zA-Z]{2,63}$)', re.I | re.S | re.M)
        return bool(re.match(fqdn_re,fqdn))
    except:
        return False


def genMeteorID():
    return('%024x' % random.randrange(16**24))


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

        self.registration = ['blockfqdn']
        self.priority = 10
        self.name = "FQDNBlockList"
        self.description = "FQDN Block LIst"

        # set my own conf file
        # relative path to the rest index.py file
        self.configfile = './plugins/fqdnblocklist.conf'
        self.options = None
        if os.path.exists(self.configfile):
            sys.stdout.write('found conf file {0}\n'.format(self.configfile))
        self.initConfiguration()

    def parse_fqdn_whitelist(self, fqdn_whitelist_location):
        fqdns = []
        with open(fqdn_whitelist_location, "r") as text_file:
            for line in text_file:
                line=line.strip().strip("'").strip('"')
                if isFQDN(line):
                    fqdns.append(line)
        return fqdns

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

        # FQDN whitelist as a comma separted list of example.com or foo.bar.com style names
        self.options.fqdn_whitelist_file = getConfig('fqdn_whitelist_file', '/dev/null', self.configfile)

        # optional statuspage.io integration
        self.options.statuspage_api_key = getConfig(
            'statuspage_api_key',
            '',
            self.configfile)
        self.options.statuspage_page_id = getConfig(
            'statuspage_page_id',
            '',
            self.configfile)
        self.options.statuspage_url = 'https://api.statuspage.io/v1/pages/{0}/incidents.json'.format(
            self.options.statuspage_page_id)
        self.options.statuspage_component_id = getConfig(
            'statuspage_component_id',
            '',
            self.configfile)
        self.options.statuspage_sub_component_id = getConfig(
            'statuspage_sub_component_id',
            '',
            self.configfile)

    def blockFQDN(self, fqdn=None, comment=None, duration=None, referenceID=None, userID=None):
        try:
            # DB connection/table
            mongoclient = MongoClient(self.options.mongohost, self.options.mongoport)
            fqdnblocklist = mongoclient.meteor['fqdnblocklist']

            # good data?
            if isFQDN(fqdn):

                # already in the table?
                fqdnblock = fqdnblocklist.find_one({'fqdn': fqdn})
                if fqdnblock is None:
                    # insert
                    fqdnblock= dict()
                    fqdnblock['_id'] = genMeteorID()
                    fqdnblock['fqdn']= fqdn
                    fqdnblock['dateAdded'] = datetime.utcnow()
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
                    fqdnblock['dateExpiring'] = end_date
                    fqdnblock['comment'] = comment
                    fqdnblock['creator'] = userID
                    fqdnblock['reference'] = referenceID
                    ref = fqdnblocklist.insert(fqdnblock)
                    sys.stdout.write('{0} written to db\n'.format(ref))
                    sys.stdout.write('%s: added to the fqdnblocklist table\n' % (fqdn))

                    # send to statuspage.io?
                    if len(self.options.statuspage_api_key) > 1:
                        try:
                            headers = {'Authorization': 'Oauth {0}'.format(self.options.statuspage_api_key)}
                            # send the data as a form post per:
                            # https://doers.statuspage.io/api/v1/incidents/#create-realtime
                            post_data = {
                                'incident[name]': 'block FQDN {}'.format(fqdn),
                                'incident[status]': 'resolved',
                                'incident[impact_override]': 'none',
                                'incident[body]': '{} initiated a block of FDQN {} until {}'.format(
                                    userID,
                                    fqdn,
                                    end_date.isoformat()),
                                'incident[component_ids][]': self.options.statuspage_sub_component_id,
                                'incident[components][{0}]'.format(self.options.statuspage_component_id): "operational"
                            }
                            response = requests.post(self.options.statuspage_url,
                                                     headers=headers,
                                                     data=post_data)
                            if response.ok:
                                sys.stdout.write('%s: notification sent to statuspage.io\n' % (fqdn))
                            else:
                                sys.stderr.write('%s: statuspage.io notification failed %s\n' % (fqdn, response.json()))
                        except Exception as e:
                            sys.stderr.write('Error while notifying statuspage.io for %s: %s\n' %(fqdn, e))
                else:
                    sys.stderr.write('%s: is already present in the fqdnblocklist table\n' % (fqdn))
            else:
                sys.stderr.write('%s: is not a valid fqdn\n' % (fqdn))
        except Exception as e:
            sys.stderr.write('Error while blocking %s: %s\n' % (fqdn, e))

    def onMessage(self, request, response):
        '''
        request: http://bottlepy.org/docs/dev/api.html#the-request-object
        response: http://bottlepy.org/docs/dev/api.html#the-response-object

        '''
        response.headers['X-PLUGIN'] = self.description

        # Refresh the whitelist each time we get a message
        self.options.fqdnwhitelist = self.parse_fqdn_whitelist(self.options.fqdn_whitelist_file)

        fqdn = None
        comment = None
        duration = None
        referenceID = None
        userid = None
        blockfqdn = False

        # loop through the fields of the form
        # and fill in our values
        try:
            for i in request.json:
                # were we checked?
                if self.name in i:
                    blockfqdn = i.values()[0]
                if 'fqdn' in i:
                    fqdn = i.values()[0]
                if 'duration' in i:
                    duration = i.values()[0]
                if 'comment' in i:
                    comment = i.values()[0]
                if 'referenceid' in i:
                    referenceID = i.values()[0]
                if 'userid' in i:
                    userid = i.values()[0]

            if blockfqdn and fqdn is not None:
                if isFQDN(fqdn):
                        whitelisted = False
                        for whitelist_fqdn in self.options.fqdnwhitelist:
                            if fqdn == whitelist_fqdn:
                                whitelisted = True
                                sys.stdout.write('{0} is whitelisted as part of {1}\n'.format(fqdn, whitelist_fqdn))

                        if not whitelisted:
                            self.blockFQDN(
                                fqdn,
                                comment,
                                duration,
                                referenceID,
                                userid
                            )
                            sys.stdout.write('added {0} to blocklist\n'.format(fqdn))
                        else:
                            sys.stdout.write('not adding {0} to blocklist, it was found in whitelist\n'.format(fqdn))
                else:
                    sys.stdout.write('not adding {0} to blocklist, invalid fqdn\n'.format(fqdn))
                    response.status = "400 invalid FQDN"
                    response.body = "invalid FQDN"
        except Exception as e:
            sys.stderr.write('Error handling request.json %r \n' % (e))
            response.status = "500"

        return (request, response)
