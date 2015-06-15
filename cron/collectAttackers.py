#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
# Copyright (c) 2014 Mozilla Corporation
#
# Contributors:
# Jeff Bryner jbryner@mozilla.com

import calendar
import collections
import json
import logging
import pyes
import pytz
import random
import netaddr
import sys
from bson.son import SON
from datetime import datetime
from datetime import timedelta
from configlib import getConfig, OptionParser
from kombu import Connection, Queue, Exchange
from logging.handlers import SysLogHandler
from dateutil.parser import parse
from pymongo import MongoClient
from pymongo import collection
from collections import Counter

logger = logging.getLogger(sys.argv[0])


def loggerTimeStamp(self, record, datefmt=None):
    return toUTC(datetime.now()).isoformat()


def initLogger():
    logger.level = logging.INFO
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    formatter.formatTime = loggerTimeStamp
    if options.output == 'syslog':
        logger.addHandler(
            SysLogHandler(
                address=(options.sysloghostname, options.syslogport)))
    else:
        sh = logging.StreamHandler(sys.stderr)
        sh.setFormatter(formatter)
        logger.addHandler(sh)


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


def toUTC(suspectedDate, localTimeZone=None):
    '''make a UTC date out of almost anything'''
    utc = pytz.UTC
    objDate = None
    if localTimeZone is None:
        localTimeZone=options.defaulttimezone    
    if type(suspectedDate) in (str, unicode):
        objDate = parse(suspectedDate, fuzzy=True)
    elif type(suspectedDate) == datetime:
        objDate = suspectedDate

    if objDate.tzinfo is None:
        objDate = pytz.timezone(localTimeZone).localize(objDate)
        objDate = utc.normalize(objDate)
    else:
        objDate = utc.normalize(objDate)
    if objDate is not None:
        objDate = utc.normalize(objDate)

    return objDate


def genMeteorID():
    return('%024x' % random.randrange(16**24))


def keypaths(nested):
    ''' return a list of nested dict key paths
        like: [u'_source', u'details', u'hostname']
    '''
    for key, value in nested.iteritems():
        if isinstance(value, collections.Mapping):
            for subkey, subvalue in keypaths(value):
                yield [key] + subkey, subvalue
        else:
            yield [key], value


def dictpath(path):
    ''' split a string representing a
        nested dictionary path key.subkey.subkey
    '''
    for i in path.split('.'):
        yield '{0}'.format(i)


def mostCommon(listofdicts,dictkeypath):
    """
        Given a list containing dictionaries,
        return the most common entries
        along a key path separated by .
        i.e. dictkey.subkey.subkey
        returned as a list of tuples
        [(value,count),(value,count)]
    """
    inspectlist=list()
    path=list(dictpath(dictkeypath))
    for i in listofdicts:
        for k in list(keypaths(i)):
            if not (set(k[0]).symmetric_difference(path)):
                inspectlist.append(k[1])

    return Counter(inspectlist).most_common()


def searchESForBROAttackers(es, threshold):
    begindateUTC = toUTC(datetime.now() - timedelta(hours=2))
    enddateUTC = toUTC(datetime.now())
    qDate = pyes.RangeQuery(qrange=pyes.ESRange('utctimestamp', from_value=begindateUTC, to_value=enddateUTC))
    q = pyes.ConstantScoreQuery(pyes.MatchAllQuery())
    qBro = pyes.QueryFilter(pyes.MatchQuery('category', 'bro_notice', 'phrase'))
    qErr = pyes.QueryFilter(pyes.MatchQuery('details.note', 'MozillaHTTPErrors::Excessive_HTTP_Errors_Attacker', 'phrase'))
    q = pyes.FilteredQuery(q, pyes.BoolFilter(must=[qBro, qErr]))

    results = es.search(q, size=1000, indices='events,events-previous')
    # grab results as native es results to avoid pyes iteration bug
    # and get easier access to es metadata fields
    rawresults = results._search_raw()['hits']['hits']
    
    # Hit count is buried in the 'sub' field
    # as: 'sub': u'6 in 1.0 hr, eps: 0'
    # cull the records for hitcounts over the threshold before returning
    attackers = list()
    for r in rawresults:
        hitcount = int(r['_source']['details']['sub'].split()[0])
        if hitcount > threshold:
            attackers.append(r)
    return attackers

def searchMongoAlerts(mozdefdb):
    attackers=mozdefdb['attackers']
    alerts=mozdefdb['alerts']
    # search the last X alerts for IP addresses
    # aggregated by CIDR mask/24
    
    # aggregate IPv4 addresses in the most recent alerts
    # to find common attackers.
    ipv4TopHits = alerts.aggregate([
        {"$sort": {"utcepoch":-1}}, # reverse sort the current alerts
        {"$limit": 100}, #most recent 100
        {"$match": {"events.documentsource.details.sourceipaddress":{"$exists": True}}}, # must have an ip address
        {"$match": {"attackerid":{"$exists": False}}}, # must not be already related to an attacker
        {"$unwind":"$events"}, #make each event into it's own doc
        {"$project":{"_id":0,
                     "sourceip":"$events.documentsource.details.sourceipaddress"}}, #emit the source ip only
        {"$group": {"_id": "$sourceip", "hitcount": {"$sum": 1}}}, # count by ip
        {"$match":{"hitcount":{"$gt":5}}}, # limit to those with X observances
        {"$sort": SON([("hitcount", -1), ("_id", -1)])}, # sort 
        {"$limit": 10} # top 10
        ])
    for ip in ipv4TopHits['result']:
        #sanity check ip['_id'] which should be the ipv4 address
        if isIPv4(ip['_id']) and ip['_id'] not in netaddr.IPSet(['0.0.0.0']):
            ipcidr = netaddr.IPNetwork(ip['_id'])
            # expand it to a /24 CIDR
            # todo: lookup ipwhois for asn_cidr value
            # potentially with a max mask value (i.e. asn is /8, limit attackers to /24)
            ipcidr.prefixlen = 24
    
            # append to or create attacker.
            # does this match an existing attacker's indicators
            if not ipcidr.ip.is_loopback() and not ipcidr.ip.is_private() and not ipcidr.ip.is_reserved():
                logger.debug('searching for alert ip ' + str(ipcidr))
                attacker = attackers.find_one({'indicators.ipv4address': str(ipcidr)})

                if attacker is None:
                    # new attacker
                    # generate a meteor-compatible ID
                    # save the ES document type, index, id
                    # and add a sub list for future events
                    logger.debug('new attacker from alerts')
                    newAttacker = genNewAttacker()

                    # str to get the ip/cidr rather than netblock cidr.
                    # i.e. '1.2.3.4/24' not '1.2.3.0/24'
                    newAttacker['indicators'].append(dict(ipv4address=str(ipcidr)))
                    matchingalerts = alerts.find(
                        {"events.documentsource.details.sourceipaddress":
                         str(ipcidr.ip),
                         })
                    if matchingalerts is not None:
                        # update list of alerts this attacker matched.
                        for alert in matchingalerts:
                            newAttacker['alerts'].append(
                                dict(alertid=alert['_id'])
                            )
                            # update alert with attackerID
                            alert['attackerid'] = newAttacker['_id']
                            alerts.save(alert)
                            
                            #add the events from this alert:
                            #add the events from this alert:
                            for e in alert['events']:
                                newAttacker['events'].append(e)
                    newAttacker['alertscount'] = len(newAttacker['alerts'])
                    newAttacker['eventscount'] = len(newAttacker['events'])
                    if newAttacker['eventscount'] > 0:
                        newAttacker['lastseentimestamp'] = toUTC(newAttacker['events'][-1]['documentsource']['utctimestamp'], 'UTC')
                    attackers.insert(newAttacker)
                    #upate geoIP info
                    latestGeoIP = [a['events'] for a in alerts.find(
                        {"events.documentsource.details.sourceipaddress":
                         str(ipcidr.ip),
                         })][-1][0]['documentsource']
                    updateAttackerGeoIP(mozdefdb, newAttacker['_id'], latestGeoIP)
                    
                    if options.broadcastattackers:
                        broadcastAttacker(newAttacker)

                else:
                    logger.debug('found existing attacker in alerts')
                    # if alert not present in this attackers list
                    # append this to the list
                    # todo: trim the list at X (i.e. last 100)
                    # search alerts without attackerid
                    matchingalerts = alerts.find(
                        {"events.documentsource.details.sourceipaddress":
                         str(ipcidr.ip),
                         "attackerid":{"$exists": False}
                         })
                    if matchingalerts is not None:
                        #attacker['eventscount'] = len(attacker['events'])
                        logger.debug('matched alert with attacker')
                        
                        # update list of alerts this attacker matched.
                        for alert in matchingalerts:
                            attacker['alerts'].append(
                                dict(alertid=alert['_id'])
                            )
                            # update alert with attackerID
                            alert['attackerid'] = attacker['_id']
                            alerts.save(alert)
                            #add the events from this alert:
                            for e in alert['events']:
                                attacker['events'].append(e)
                            
                            # geo ip could have changed, update it
                            # to the latest
                            updateAttackerGeoIP(mozdefdb, attacker['_id'], alert['events'][-1]['documentsource'])
                        
                        # update last seen time
                        attacker['lastseentimestamp'] = toUTC(attacker['events'][-1]['documentsource']['utctimestamp'], 'UTC')
                        # update counts
                        attacker['alertscount'] = len(attacker['alerts'])
                        attacker['eventscount'] = len(attacker['events'])
                        attackers.save(attacker)

                    # should we autocategorize the attacker
                    # based on their alerts? 
                    if attacker['category'] == 'unknown' and options.autocategorize:
                        # take a look at recent alerts for this attacker
                        # and if they are all the same category
                        # auto-categorize the attacker
                        matchingalerts = alerts.find(
                            {"attackerid":attacker['_id']}
                             ).sort('utcepoch', -1).limit(50)
                        # summarize the alert categories
                        # returns list of tuples: [(u'bruteforce', 8)]
                        categoryCounts= mostCommon(matchingalerts,'category')

                        #are the alerts all the same category?
                        if len(categoryCounts) == 1:
                            #is the alert category mapped to an attacker category?
                            for category in options.categorymapping:
                                if category.keys()[0] == categoryCounts[0][0]:
                                    attacker['category'] = category[category.keys()[0]]
                                    attackers.save(attacker)
                                    
                        
def broadcastAttacker(attacker):
    '''
    send this attacker info to our message queue
    '''
    try:
        connString = 'amqp://{0}:{1}@{2}:{3}/{4}'.format(options.mquser,
                                                         options.mqpassword,
                                                         options.mqserver,
                                                         options.mqport,
                                                         options.mqvhost)
        if options.mqprotocol == 'amqps':
            mqSSL = True
        else:
            mqSSL = False
        mqConn = Connection(connString, ssl=mqSSL)

        alertExchange = Exchange(
            name=options.alertexchange,
            type='topic',
            durable=True)
        alertExchange(mqConn).declare()
        mqproducer = mqConn.Producer(serializer='json')
        
        logger.debug('Kombu configured')
    except Exception as e:
        logger.error('Exception while configuring kombu for alerts: {0}'.format(e))
    try:
        # generate an 'alert' structure for this attacker:
        mqAlert = dict(severity='NOTICE', category='attacker')
    
        if 'datecreated' in attacker.keys():
            mqAlert['utctimestamp'] = attacker['datecreated'].isoformat()
    
        mqAlert['summary'] = 'New Attacker: {0} events: {1}, alerts: {2}'.format(attacker['indicators'], attacker['eventscount'], attacker['alertscount'])
        logger.debug(mqAlert)
        ensurePublish = mqConn.ensure(
            mqproducer,
            mqproducer.publish,
            max_retries=10)
        ensurePublish(mqAlert,
            exchange=alertExchange,
            routing_key=options.routingkey)
    except Exception as e:
        logger.error('Exception while publishing attacker: {0}'.format(e))
        

def genNewAttacker():
    newAttacker = dict()
    newAttacker['_id'] = genMeteorID()
    newAttacker['lastseentimestamp'] = toUTC(datetime.now())
    newAttacker['firstseentimestamp'] = toUTC(datetime.now())
    newAttacker['events'] = list()
    newAttacker['eventscount'] = 0
    newAttacker['alerts'] = list()
    newAttacker['alertscount'] = 0
    newAttacker['category'] = 'unknown'
    newAttacker['score'] = 0
    newAttacker['geocoordinates'] = dict(countrycode='', longitude=0, latitude=0)
    newAttacker['tags'] = list()
    newAttacker['notes'] = list()
    newAttacker['indicators'] = list()
    newAttacker['attackphase'] = 'unknown'
    newAttacker['datecreated'] = toUTC(datetime.now())
    newAttacker['creator'] = sys.argv[0]
    
    return newAttacker

def updateAttackerGeoIP(mozdefdb, attackerID, eventDictionary):
    '''given an attacker ID and a dictionary of an elastic search event
       look for a valid geoIP in the dict and update the attacker's geo coordinates
    '''

    # geo ip should be in eventDictionary['details']['sourceipgeolocation']
    #"sourceipgeolocation": {
      #"city": "Polska",
      #"region_code": "73",
      #"area_code": 0,
      #"time_zone": "Europe/Warsaw",
      #"dma_code": 0,
      #"metro_code": null,
      #"country_code3": "POL",
      #"latitude": 52.59309999999999,
      #"postal_code": null,
      #"longitude": 19.089400000000012,
      #"country_code": "PL",
      #"country_name": "Poland",
      #"continent": "EU"
    #logger.debug(eventDictionary)
    if 'details' in eventDictionary.keys():
        if  'sourceipgeolocation' in eventDictionary['details']:
            attackers=mozdefdb['attackers']
            attacker = attackers.find_one({'_id': attackerID})
            if attacker is not None:
                attacker['geocoordinates'] = dict(countrycode='',
                                                  longitude=0,
                                                  latitude=0)
                if 'country_code' in eventDictionary['details']['sourceipgeolocation'].keys():
                    attacker['geocoordinates']['countrycode'] = eventDictionary['details']['sourceipgeolocation']['country_code']
                if 'longitude' in eventDictionary['details']['sourceipgeolocation'].keys():
                    attacker['geocoordinates']['longitude'] = eventDictionary['details']['sourceipgeolocation']['longitude']
                if 'latitude' in eventDictionary['details']['sourceipgeolocation'].keys():
                    attacker['geocoordinates']['latitude'] = eventDictionary['details']['sourceipgeolocation']['latitude']
                attackers.save(attacker)
    else:
        logger.debug('no details in the dictionary')
        logger.debug(eventDictionary)
                
    

def updateMongoWithESEvents(mozdefdb, results):
    attackers=mozdefdb['attackers']
    for r in results:
        if 'sourceipaddress' in r['_source']['details']:
            if netaddr.valid_ipv4(r['_source']['details']['sourceipaddress']):
                sourceIP = netaddr.IPNetwork(r['_source']['details']['sourceipaddress'])
                # expand it to a /24 CIDR
                # todo: lookup ipwhois for asn_cidr value
                # potentially with a max mask value (i.e. asn is /8, limit attackers to /24)
                sourceIP.prefixlen = 24                
                if not sourceIP.ip.is_loopback() and not sourceIP.ip.is_private() and not sourceIP.ip.is_reserved():
                    esrecord = dict(documentid=r['_id'],
                         documenttype=r['_type'],
                         documentindex=r['_index'],
                         documentsource=r['_source'])
                
                    logger.debug('searching for ' + str(sourceIP))
                    #attacker = attackers.find_one({'events.details.sourceipaddress': str(sourceIP.ip)})
                    attacker = attackers.find_one({'indicators.ipv4address': str(sourceIP)})
                    if attacker is None:
                        # new attacker
                        # generate a meteor-compatible ID
                        # save the ES document type, index, id
                        # and add a sub list for future events
                        logger.debug('new attacker')
                        newAttacker = genNewAttacker()

                        #expand the source ip to a /24 for the indicator match.
                        sourceIP.prefixlen = 24
                        # str sourceIP to get the ip/cidr rather than netblock cidr.
                        newAttacker['indicators'].append(dict(ipv4address=str(sourceIP)))
                        newAttacker['events'].append(esrecord)
                        newAttacker['eventscount'] = len(newAttacker['events'])

                        attackers.insert(newAttacker)
                        updateAttackerGeoIP(mozdefdb, newAttacker['_id'], esrecord['documentsource'])
                    else:
                        # if event not present in this attackers events
                        # append this to the list of events
                        # todo: trim the list at X (i.e. last 100 events)
                        matchingevent = attackers.find_one(
                            {'_id': attacker['_id'],
                             'events.documentid': r['_id'],
                             'events.documenttype': r['_type'],
                             'events.documentindex': r['_index']
                             })
                        if matchingevent is None: 
                            attacker['events'].append(esrecord)
                            attacker['eventscount'] = len(attacker['events'])
                            logger.debug('new event found for matching attacker')
                            attacker['lastseentimestamp'] = attacker['events'][-1]['documentsource']['utctimestamp']
                            attackers.save(attacker)
                        # geo ip could have changed, update it
                        updateAttackerGeoIP(mozdefdb, attacker['_id'], esrecord['documentsource'])


def main():
    logger.debug('starting')
    logger.debug(options)
    try:
        es = pyes.ES(server=(list('{0}'.format(s) for s in options.esservers)))
        client = MongoClient(options.mongohost, options.mongoport)
        # use meteor db
        mozdefdb = client.meteor
        esResults = searchESForBROAttackers(es, 100)
        updateMongoWithESEvents(mozdefdb, esResults)
        searchMongoAlerts(mozdefdb)

    except ValueError as e:
        logger.error("Exception %r collecting attackers to mongo" % e)


def initConfig():
    #change this to your default timezone
    options.defaulttimezone=getConfig('defaulttimezone','UTC',options.configfile)
    # output our log to stdout or syslog
    options.output = getConfig('output', 'stdout', options.configfile)
    # syslog hostname
    options.sysloghostname = getConfig('sysloghostname',
                                       'localhost',
                                       options.configfile)
    # syslog port
    options.syslogport = getConfig('syslogport', 514, options.configfile)

    # elastic search server settings
    options.esservers = list(getConfig('esservers',
                                       'http://localhost:9200',
                                       options.configfile).split(','))
    options.mongohost = getConfig('mongohost', 'localhost', options.configfile)
    options.mongoport = getConfig('mongoport', 3001, options.configfile)

    # should we automatically categorize
    # new attackers based on their alerts? 
    options.autocategorize = getConfig('autocategorize', False, options.configfile)
    # get the mapping of alert category to attacker category
    # supply as a list of dicts: 
    # [{"bruteforce":"bruteforcer"},{"alertcategory":"attackercategory"}]
    options.categorymapping = json.loads(getConfig('categorymapping', "[]", options.configfile))
    
    # should we broadcast new attackers
    # to a message queue?
    options.broadcastattackers = getConfig('broadcastattackers', False, options.configfile)
    # message queue options
    options.mqserver = getConfig('mqserver', 'localhost', options.configfile)
    options.alertexchange = getConfig('alertexchange', 'alerts', options.configfile)
    options.routingkey = getConfig('routingkey', 'mozdef.alert', options.configfile)
    options.mquser = getConfig('mquser', 'guest', options.configfile)
    options.mqpassword = getConfig('mqpassword', 'guest', options.configfile)
    options.mqport = getConfig('mqport', 5672, options.configfile)
    options.mqvhost = getConfig('mqvhost', '/', options.configfile)
    # set to either amqp or amqps for ssl
    options.mqprotocol = getConfig('mqprotocol', 'amqp', options.configfile)

if __name__ == '__main__':
    parser = OptionParser()
    parser.add_option(
        "-c",
        dest='configfile',
        default=sys.argv[0].replace('.py', '.conf'),
        help="configuration file to use")
    (options, args) = parser.parse_args()
    initConfig()
    initLogger()
    main()
