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

def esCloudTrailSearch(es,begindateUTC=None, enddateUTC=None):
    resultsList=list()
    if begindateUTC is None:
        begindateUTC=toUTC(datetime.now() - timedelta(hours=160))
    if enddateUTC is None:
        enddateUTC= toUTC(datetime.now())
    try:
        #search for actions within the date range that haven't already been alerted (i.e. given an alerttimestamp)
        qDate=pyes.RangeQuery(qrange=pyes.ESRange('utctimestamp',from_value=begindateUTC,to_value=enddateUTC))
        qcloud=pyes.TermFilter('_type','cloudtrail')
        qEvents=pyes.TermsFilter('eventName',['runinstances','stopinstances','startinstances'])
        qalerted=pyes.ExistsFilter('alerttimestamp')
        results=es.search(pyes.ConstantScoreQuery(pyes.BoolFilter(must=[qcloud,qDate,qEvents],must_not=[qalerted])), indices='events')
        #uncomment for debugging to recreate alerts for events that already have an alerttimestamp
        #results=es.search(pyes.ConstantScoreQuery(pyes.BoolFilter(must=[qcloud,qDate,qEvents])))
        return(results._search_raw()['hits']['hits'])
        
    except pyes.exceptions.NoServerAvailable:
        logger.error('Elastic Search server could not be reached, check network connectivity')
        
def createAlerts(es,esResults):
    try:
        if len(esResults)>0:
            for r in esResults:
                alert=dict(utctimestamp=toUTC(datetime.now()).isoformat(),severity='INFO',summary='',category='AWSCloudtrail',tags=['cloudtrail','aws'],eventsource=[],events=[])
                alert['events'].append(
                    dict(documentindex=r['_index'],
                         documenttype=r['_type'],
                         documentsource=r['_source'], 
                         documentid=r['_id']))
                alert['eventtimestamp']=r['_source']['eventTime']
                alert['severity']='INFO'
                alert['summary']=('{0} called {1} from {2}'.format(r['_source']['userIdentity']['userName'],r['_source']['eventName'],r['_source']['sourceIPAddress']))
                alert['eventsource']=flattenDict(r)
                if r['_source']['eventName']=='RunInstances':
                    if isinstance(r['_source']['responseElements'], dict) and 'instancesSet' in r['_source']['responseElements'].keys():
                        for i in r['_source']['responseElements']['instancesSet']['items']:
                            if 'privateDnsName' in i.keys():
                                alert['summary'] += (' running {0} '.format(i['privateDnsName']))
                            elif 'instanceId' in i.keys():
                                alert['summary'] += (' running {0} '.format(i['instanceId']))
                            else:
                                alert['summary'] += (' running {0} '.format(flattenDict(i)))
                if r['_source']['eventName']=='StartInstances':
                    for i in r['_source']['requestParameters']['instancesSet']['items']:
                        alert['summary'] += (' starting {0} '.format(i['instanceId']))                
                logger.debug(alert['summary'])
                #logger.debug(alert['events'])
                
                #save alert to alerts index, update events index with alert ID for cross reference
                alertResult=alertToES(es,alert)
                logger.debug(alertResult)
                if 'alerts' not in r['_source'].keys():
                    r['_source']['alerts']=[]
                r['_source']['alerts'].append(dict(index=alertResult['_index'],type=alertResult['_type'],id=alertResult['_id']))
                r['_source']['alerttimestamp']=toUTC(datetime.now()).isoformat()
                es.update(r['_index'],r['_type'],r['_id'],document=r['_source'])
                alertToMessageQueue(alert)
    except EOFError as e:
        logger.error("Exception %r when creating alerts "%e)
        
def main():
    logger.debug('starting')
    logger.debug(options)
    es=pyes.ES((list('{0}'.format(s) for s in options.esservers)))
    results=esCloudTrailSearch(es)
    createAlerts(es,results)
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
