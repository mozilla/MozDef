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
import MySQLdb
from datetime import datetime, timedelta
import json
import netaddr

def isIPv4(ip):
    try:
        # netaddr on it's own considers 1 and 0 to be valid_ipv4
        # so a little sanity check prior to netaddr.
        # Use IPNetwork instead of valid_ipv4 to allow CIDR
        if '.' in ip and len(ip.split('.'))==4:
            # some ips are quoted
            netaddr.IPNetwork(ip.strip("'").strip('"'))
            return True
        else:
            return False
    except:
        return False


def isIPv6(ip):
    try:
        return netaddr.valid_ipv6(ip)
    except:
        return False


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

        self.registration = ['blockip']
        self.priority = 10
        self.name = "Banhammer"
        self.description = "BGP Blackhole"

        # set my own conf file
        # relative path to the rest index.py file
        self.configfile = './plugins/banhammer.conf'
        self.options = None
        if os.path.exists(self.configfile):
            sys.stdout.write('found conf file {0}\n'.format(self.configfile))
            self.initConfiguration()
        

    def initConfiguration(self):
        myparser = OptionParser()
        # setup self.options by sending empty list [] to parse_args
        (self.options, args) = myparser.parse_args([])
        
        # fill self.options with plugin-specific options
        # change this to your default zone for when it's not specified
        self.options.defaultTimeZone = getConfig('defaulttimezone', 'US/Pacific', self.configfile)
        
        # options for your custom/internal ip blocking service
        # mozilla's is called banhammer
        # and uses an intermediary mysql DB
        # here we set credentials
        self.options.banhammerdbhost = getConfig(
            'banhammerdbhost',
            'localhost',
            self.configfile)
        self.options.banhammerdbuser = getConfig(
            'banhammerdbuser',
            'auser',
            self.configfile)
        self.options.banhammerdbpasswd = getConfig(
            'banhammerdbpasswd',
            '',
            self.configfile)
        self.options.banhammerdbdb = getConfig(
            'banhammerdbdb',
            'banhammer',
            self.configfile)


    def banhammer(self,
                  ipaddress = None,
                  CIDR = None, 
                  comment = None, 
                  duration = None, 
                  referenceID = None,
                  userID=None
                  ):
        try:
            mysqlconn = MySQLdb.connect(
                host=self.options.banhammerdbhost,
                user=self.options.banhammerdbuser,
                passwd=self.options.banhammerdbpasswd,
                db=self.options.banhammerdbdb)
            dbcursor = mysqlconn.cursor()
            # Look if attacker already in the DB, if yes get id
            dbcursor.execute("""SELECT id FROM blacklist_offender
                  WHERE address = "%s" AND cidr = %d""" % (ipaddress, int(CIDR)))
            qresult = dbcursor.fetchone()
            if not qresult:
                # insert new attacker in banhammer DB
                created_date = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
                dbcursor.execute("""
                    INSERT INTO blacklist_offender(address, cidr)
                    VALUES ("%s", %d)
                """ % (ipaddress, int(CIDR)))
                # get the ID of this query
                dbcursor.execute("""SELECT id FROM blacklist_offender
                  WHERE address = "%s" AND cidr = %d""" % (ipaddress, int(CIDR)))
                qresult = dbcursor.fetchone()
            (attacker_id,) = qresult
            # Compute start and end dates
            start_date = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
            end_date = datetime.utcnow() + timedelta(hours=1)
            if duration == '12hr':
                end_date = datetime.utcnow() + timedelta(hours=12)
            elif duration == '1d':
                end_date = datetime.utcnow() + timedelta(days=1)
            elif duration == '1w':
                end_date = datetime.utcnow() + timedelta(days=7)
            elif duration == '30d':
                end_date = datetime.utcnow() + timedelta(days=30)
    
            if referenceID is not None:
                # Insert in DB
                dbcursor.execute("""
                    INSERT INTO blacklist_blacklist(offender_id, start_date, end_date, comment, reporter, bug_number)
                    VALUES (%d, "%s", "%s", "%s", "%s", %d)
                    """ % (attacker_id, start_date, end_date, comment, userID, int(referenceID)))
            else:
                dbcursor.execute("""
                    INSERT INTO blacklist_blacklist(offender_id, start_date, end_date, comment, reporter)
                    VALUES (%d, "%s", "%s", "%s", "%s")
                    """ % (attacker_id, start_date, end_date, comment, userID))
            mysqlconn.commit()
            sys.stderr.write('%s/%d: banhammered\n' % (ipaddress, int(CIDR)))
        except Exception as e:
            sys.stderr.write('Error while banhammering %s/%d: %s\n' % (ipaddress, int(CIDR), e))


    def onMessage(self, request, response):
        '''
        request: http://bottlepy.org/docs/dev/api.html#the-request-object
        response: http://bottlepy.org/docs/dev/api.html#the-response-object
        
        '''
        response.headers['X-PLUGIN'] = self.description
        # debug
        # print(request.json)
        
        #format/validate request.json for banhammer:
        ipaddress = None
        CIDR = None
        comment = None
        duration = None
        referenceID = None
        userid = None
        banhammer = False
        
        # loop through the fields of the form
        # and fill in our values
        try: 
            for i in request.json:
                # were we checked?
                if self.name in i.keys():
                    banhammer = i.values()[0]
                if 'ipaddress' in i.keys():
                    ipaddress = i.values()[0]
                if 'duration' in i.keys():
                    duration = i.values()[0]
                if 'comment' in i.keys():
                    comment = i.values()[0]
                if 'referenceID' in i.keys():
                    referenceID = i.values()[0]
                if 'userid' in i.keys():
                    userid = i.values()[0]

            if banhammer and ipaddress is not None:
                #figure out the CIDR mask
                if isIPv4(ipaddress) or isIPv6(ipaddress):
                    ipcidr=netaddr.IPNetwork(ipaddress)
                    if not ipcidr.ip.is_loopback() \
                       and not ipcidr.ip.is_private() \
                       and not ipcidr.ip.is_reserved():
                        #split the ip vs cidr mask
                        ipaddress, CIDR =  str(ipcidr.cidr).split('/')
                        self.banhammer(ipaddress,
                                       CIDR, 
                                       comment, 
                                       duration, 
                                       referenceID,
                                       userid)
                        sys.stdout.write ('Sent {0}/{1} to banhammer\n'.format(ipaddress, CIDR))
        except Exception as e:
            sys.stderr.write('Error handling request.json %r \n'% (e))
                
        return (request, response)
