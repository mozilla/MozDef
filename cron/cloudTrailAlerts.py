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
from configlib import getConfig, OptionParser
from logging.handlers import SysLogHandler
import logging
from datetime import datetime

import sys
import os
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../lib'))
from utilities.toUTC import toUTC
from elasticsearch_client import ElasticsearchClient, ElasticsearchBadServer
from query_models import SearchQuery, TermMatch, TermsMatch, ExistsMatch

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
        res = es.save_alert(body=alertDict)
        return(res)
    except ElasticsearchBadServer:
        logger.error('Elastic Search server could not be reached, check network connectivity')

def esCloudTrailSearch(es):
    search_query = SearchQuery(hours=160)
    search_query.add_must([
        TermMatch('_type', 'cloudtrail'),
        TermsMatch('eventName', ['runinstances', 'stopinstances', 'startinstances']),
    ])
    search_query.add_must_not(ExistsMatch('alerttimestamp'))
    try:
        full_results = search_query.execute(es)
        return full_results['hits']

    except ElasticsearchBadServer:
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
                es.save_object(index=r['_index'], doc_type=r['_type'], doc_id=r['_id'], body=r['_source'])
                alertToMessageQueue(alert)
    except EOFError as e:
        logger.error("Exception %r when creating alerts "%e)

def main():
    logger.debug('starting')
    logger.debug(options)
    es = ElasticsearchClient((list('{0}'.format(s) for s in options.esservers)))
    results = esCloudTrailSearch(es)
    createAlerts(es, results)
    logger.debug('finished')

def initConfig():
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
