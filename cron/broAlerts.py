#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
# Copyright (c) 2014 Mozilla Corporation
#
# Contributors:
# Jeff Bryner jbryner@mozilla.com

import pika
import sys
import json
from configlib import getConfig,OptionParser
from logging.handlers import SysLogHandler
import logging
from datetime import datetime
from datetime import timedelta
from dateutil.parser import parse
import pytz
import pyes
from collections import Counter

logger = logging.getLogger(sys.argv[0])

def loggerTimeStamp(self, record, datefmt=None):
    return toUTC(datetime.now()).isoformat()

def initLogger():
    logger.level=logging.INFO
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    formatter.formatTime = loggerTimeStamp
    if options.output=='syslog':    
        logger.addHandler(SysLogHandler(address=(options.sysloghostname,options.syslogport)))
    else:
        sh=logging.StreamHandler(sys.stderr)
        sh.setFormatter(formatter)
        logger.addHandler(sh)

def toUTC(suspectedDate,localTimeZone="US/Pacific"):
    '''make a UTC date out of almost anything'''
    utc=pytz.UTC
    objDate=None
    if type(suspectedDate)==str:
        objDate=parse(suspectedDate,fuzzy=True)
    elif type(suspectedDate)==datetime:
        objDate=suspectedDate
    
    if objDate.tzinfo is None:
        objDate=pytz.timezone(localTimeZone).localize(objDate)
        objDate=utc.normalize(objDate)
    else:
        objDate=utc.normalize(objDate)
    if objDate is not None:
        objDate=utc.normalize(objDate)
        
    return objDate

def flattenDict(dictIn):
    sout=''
    for k,v in dictIn.iteritems():
        sout+='{0}: {1} '.format(k,v)
    return sout

def alertToMessageQueue(alertDict):
    try:
        connection = pika.BlockingConnection(pika.ConnectionParameters(host=options.mqserver))
        channel = connection.channel()
        #declare the exchanges
        channel.exchange_declare(exchange=options.alertexchange,type='topic', durable=True)
        
        #cherry pick items from the alertDict to send to the alerts messageQueue
        mqAlert=dict(severity='INFO',category='')
        if 'severity' in alertDict.keys():
            mqAlert['severity']=alertDict['severity']
        if 'category' in alertDict.keys():
            mqAlert['category']=alertDict['category']
        if 'utctimestamp' in alertDict.keys():
            mqAlert['utctimestamp']=alertDict['utctimestamp']
        if 'eventtimestamp' in alertDict.keys():
            mqAlert['eventtimestamp']=alertDict['eventtimestamp']
        mqAlert['summary']=alertDict['summary']
        channel.basic_publish(exchange=options.alertexchange,routing_key=options.alertqueue,body=json.dumps(mqAlert))    
    except Exception as e:
        logger.error('Exception while sending alert to message queue: {0}'.format(e))

def alertToES(es,alertDict):
    try:
        res=es.index(index='alerts',doc_type='alert',doc=alertDict)
        return(res)
    except pyes.exceptions.NoServerAvailable:
        logger.error('Elastic Search server could not be reached, check network connectivity')

def esBroIntelEvents():
    begindateUTC= toUTC(datetime.now() - timedelta(minutes=30))
    enddateUTC= toUTC(datetime.now())        
    #search for events within the date range that haven't already been alerted (i.e. given an alerttimestamp)
    qDate=pyes.RangeQuery(qrange=pyes.ESRange('utctimestamp',from_value=begindateUTC,to_value=enddateUTC))
    qType=pyes.TermFilter('_type','event')
    qEvents=pyes.TermsFilter('category',['brointel'])
    qalerted=pyes.ExistsFilter('alerttimestamp')
    q=pyes.ConstantScoreQuery(pyes.MatchAllQuery())
    q.filters.append(pyes.BoolFilter(
        must=[qType, 
              qDate,
              qEvents,
              pyes.ExistsFilter('seenindicator')
        ],
        must_not=[
        qalerted
        ]))
    return q


def esBroXSSEvents():
    begindateUTC= toUTC(datetime.now() - timedelta(minutes=30))
    enddateUTC= toUTC(datetime.now())
    qDate = pyes.RangeQuery(qrange=pyes.ESRange('utctimestamp', from_value=begindateUTC, to_value=enddateUTC))
    qType = pyes.TermFilter('_type', 'event')
    qEvents = pyes.TermFilter("category","bro_xss_log")
    qalerted = pyes.ExistsFilter('alerttimestamp')
    q=pyes.ConstantScoreQuery(pyes.MatchAllQuery())
    q.filters.append(pyes.BoolFilter(
        must=[qType, 
              qDate,
              qEvents,
              pyes.ExistsFilter('uri')
        ],
        must_not=[
        qalerted
        ]))
    return q

def esRunSearch(es, query, aggregateField, detailLimit=5):
    try:
        pyesresults = es.search(query, size=1000, indices='events,events-previous')
        # logger.debug(results.count())

        # correlate any matches by the aggregate field.
        # make a simple list of indicator values that can be counted/summarized by Counter
        resultsIndicators = list()

        # bug in pyes..capture results as raw list or it mutates after first access:
        # copy the hits.hits list as our results, which is the same as the official elastic search library returns.
        results = pyesresults._search_raw()['hits']['hits']
        for r in results:
            resultsIndicators.append(r['_source']['details'][aggregateField])

        # use the list of tuples ('indicator',count) to create a dictionary with:
        # indicator,count,es records
        # and add it to a list to return.
        indicatorList = list()
        for i in Counter(resultsIndicators).most_common():
            idict = dict(indicator=i[0], count=i[1], events=[])
            for r in results:
                if r['_source']['details'][aggregateField].encode('ascii', 'ignore') == i[0]:
                    # copy events detail into this correlation up to our detail limit
                    if len(idict['events'])<detailLimit:
                        idict['events'].append(r)
            indicatorList.append(idict)
        return indicatorList

    except pyes.exceptions.NoServerAvailable:
        logger.error('Elastic Search server could not be reached, check network connectivity')  


def createAlerts(es, indicatorCounts, threshold, description):
    '''given a list of dictionaries:
        count: X
        indicator: sometext
        events: list of pyes results matching the indicator

        1) create a summary alert with detail of the events
        2) update the events with an alert timestamp so they are not included in further alerts
    '''
    try:
        if len(indicatorCounts) > 0:
            for i in indicatorCounts:
                if i['count'] > threshold:
                    alert = dict(utctimestamp=toUTC(datetime.now()).isoformat(), severity='NOTICE', summary='', category='bro', tags=['bro'], eventsource=[], events=[])
                    for e in i['events']:
                        alert['events'].append(
                            dict(documentindex=e['_index'],
                                 documenttype=e['_type'],
                                 documentsource=e['_source'],
                                 documentid=e['_id']))
                    alert['severity'] = 'NOTICE'
                    alert['summary'] = ('{0} {1}: {2}'.format(i['count'], description, i['indicator']))
                    # append first X source IPs
                    alert['summary'] += ' sample sourceips: '
                    for e in i['events'][0:3]:
                        if 'sourceipaddress' in e['_source']['details'].keys():
                            alert['summary'] += '{0} '.format(e['_source']['details']['sourceipaddress'])
                    for e in i['events']:
                        # append the relevant events in text format to avoid errant ES issues.
                        # should be able to just set eventsource to i['events'] but different versions of ES 1.0 complain
                        alert['eventsource'].append(flattenDict(e))
    
                    logger.debug(alert['summary'])
                    logger.debug(alert['events'])
                    logger.debug(alert)
    
                    # save alert to alerts index, update events index with alert ID for cross reference
                    alertResult = alertToES(es, alert)
    
                    ##logger.debug(alertResult)
                    # for each event in this list of indicatorCounts
                    # update with the alertid/index
                    # and update the alerttimestamp on the event itself so it's not re-alerted
                    for e in i['events']:
                        if 'alerts' not in e['_source'].keys():
                            e['_source']['alerts'] = []
                        e['_source']['alerts'].append(dict(index=alertResult['_index'], type=alertResult['_type'], id=alertResult['_id']))
                        e['_source']['alerttimestamp'] = toUTC(datetime.now()).isoformat()
    
                        es.update(e['_index'], e['_type'], e['_id'], document=e['_source'])
    
                    alertToMessageQueue(alert)
    except ValueError as e:
        logger.error("Exception %r when creating alerts " % e)
        
def main():
    logger.debug('starting')
    logger.debug(options)
    es=pyes.ES((list('{0}'.format(s) for s in options.esservers)))
    # search for brointel
    #indicatorCounts=esSearch(es)
    #createAlerts(es,indicatorCounts)
    
    indicatorCounts=esRunSearch(es,esBroIntelEvents(),'seenindicator', 50)
    createAlerts(es,indicatorCounts, 5, 'bro intel match')
    
    # search for xss events
    indicatorCounts=esRunSearch(es,esBroXSSEvents(),'cluster_client_ip', 50)
    createAlerts(es,indicatorCounts, 5, 'bro xss')    
    
    logger.debug('finished')

def initConfig():
    #change this to your default zone for when it's not specified
    options.defaultTimeZone=getConfig('defaulttimezone','US/Pacific',options.configfile)
    #msg queue settings
    options.mqserver=getConfig('mqserver','localhost',options.configfile)               #message queue server hostname
    options.alertqueue=getConfig('alertqueue','mozdef.alert',options.configfile)        #alert queue topic
    options.alertexchange=getConfig('alertexchange','alerts',options.configfile)        #alert queue exchange name
    #logging settings
    options.output=getConfig('output','stdout',options.configfile)                      #output our log to stdout or syslog
    options.sysloghostname=getConfig('sysloghostname','localhost',options.configfile)   #syslog hostname
    options.syslogport=getConfig('syslogport',514,options.configfile)                   #syslog port
    #elastic search server settings
    options.esservers=list(getConfig('esservers','http://localhost:9200',options.configfile).split(','))
    
if __name__ == '__main__':
    parser=OptionParser()
    parser.add_option("-c", dest='configfile' , default=sys.argv[0].replace('.py','.conf'), help="configuration file to use")
    (options,args) = parser.parse_args()
    initConfig()
    initLogger()
    main()
