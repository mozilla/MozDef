#!/usr/bin/env python
import json
import logging
import os
import pyes
import pytz
import requests
import socket
import sys
from datetime import datetime
from requests.auth import HTTPBasicAuth
from configlib import getConfig,OptionParser
from logging.handlers import SysLogHandler

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

def main():
    logger.debug('starting')
    logger.debug(options)
    es=pyes.ES(server=(list('{0}'.format(s) for s in options.esservers)))
    try: 
        auth = HTTPBasicAuth(options.mquser,options.mqpassword)

        for server in options.mqservers:
            logger.debug('checking message queues on {0}'.format(server))
            r=requests.get('http://{0}:{1}/api/queues'.format(server,options.mqapiport),auth=auth)
            mq=r.json()
            #setup a log entry for health/status.
            healthlog=dict(utctimestamp=pytz.timezone('US/Pacific').localize(datetime.now()).isoformat(),\
                        hostname=server,\
                        processid=os.getpid(),\
                        processname=sys.argv[0],\
                        severity='INFO',\
                        summary='mozdef health/status',\
                        category='mozdef',\
                        tags=[],\
                        details=[])
            
            healthlog['details']=dict(username='mozdef')
            healthlog['tags']=['mozdef','status']            
            #print(mq)
            for m in mq:
                #print('\tqueue: {0}'.format(m['name']))
                if 'message_stats' in m.keys():
                    healthlog['details'][m['name']]=dict(messages_ready=m['messages_ready'],messages_unacknowledged=m['messages_unacknowledged'])
                    #print(('\t\t{0} ready {1} unack'.format(m['messages_ready'], m['messages_unacknowledged'])))
                    
                    if 'deliver_details' in m['message_stats'].keys():
                        healthlog['details'][m['name']]['deliver_eps']=m['message_stats']['deliver_details']['rate']
                        #print('\t\t{0} in/sec, {1} out/sec'.format(m['message_stats']['publish_details']['rate'],m['message_stats']['deliver_details']['rate']))
                    if 'publish_details' in m['message_stats'].keys():
                        healthlog['details'][m['name']]['publish_eps']=m['message_stats']['publish_details']['rate']
                        #print('\t\t{0} in/sec, 0 out/sec'.format(m['message_stats']['publish_details']['rate']))
                
        
        #print(json.dumps(healthlog, sort_keys=True, indent=4))
        #post to elastic search servers directly without going through message queues
        es.index(index='events',doc_type='mozdefhealth',doc=json.dumps(healthlog),bulk=False)
    except Exception as e:
        logger.error("Exception %r when gathering health and status "%e)

def initConfig():
    options.output=getConfig('output','stdout',options.configfile)                      #output our log to stdout or syslog
    options.sysloghostname=getConfig('sysloghostname','localhost',options.configfile)   #syslog hostname
    options.syslogport=getConfig('syslogport',514,options.configfile)                   #syslog port
    
    
    #msg queue servers to check in on (list of servernames)
    options.mqservers=list(getConfig('mqservers','localhost',options.configfile).split(',')) #message queue server(s) hostname
    options.mquser=getConfig('mquser','guest',options.configfile)
    options.mqpassword=getConfig('mqpassword','guest',options.configfile)
    options.mqapiport=getConfig('mqapiport',15672,options.configfile)    #port of the rabbitmq json management interface
    
     #change this to your default zone for when it's not specified
    options.defaultTimeZone=getConfig('defaulttimezone','US/Pacific',options.configfile)
    
    #elastic search server settings
    options.esservers=list(getConfig('esservers','http://localhost:9200',options.configfile).split(','))
    
if __name__ == '__main__':
    parser=OptionParser()
    parser.add_option("-c", dest='configfile' , default=sys.argv[0].replace('.py','.conf'), help="configuration file to use")
    (options,args) = parser.parse_args()
    initConfig()
    initLogger()
    main()