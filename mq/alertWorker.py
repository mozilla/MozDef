#!/usr/bin/env python
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import pika
import sys
import json
from configlib import getConfig,OptionParser
from logging.handlers import SysLogHandler
import logging
import re
import datetime
import dateutil.parser
import pyes

logger = logging.getLogger()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def isTimeToken(token):
    info = dateutil.parser.parser().info
    if any(f(token) for f in (info.jump,info.weekday,info.month,info.hms,info.ampm,info.pertain,info.utczone,info.tzoffset)):
        return True
    try:
        float(token)
        return True
    except ValueError:
        pass
    try:
        if type(dateutil.parser.parse(token))==datetime.datetime:
            return True
    except Exception as e:
        return False
    return False

def splitTime(inString):
    '''separate a string into anything that is not a date/time token and anything that could be a time token
       useful for parsing incoming syslog to move timestamps into a separate field.
    '''
    outString=[]
    outTime=[]
    for i in inString.split():
        if isTimeToken(i):
            outTime.append(i)
        else:
            outString.append(i)
    return(' '.join(outString),' '.join(outTime))

def callback(ch, method, properties, bodyin):
    #print " [x]event %r:%r" % (method.routing_key, bodyin)

    #publish on the alerts topic queue?
    try:
        jbody=json.loads(bodyin)
        for rex in options.regexlist:
            if 'tag' in rex.keys():
                #we've been asked to limit scope to mq items with this tag
                if 'tags' in jbody.keys() and rex['tag'] not in jbody['tags']:
                    return            
            if 'summary' in jbody.keys() and re.findall(rex['expression'],jbody['summary']):
                if 'severity' in rex.keys():
                    jbody['severity']=rex['severity']
                if 'category' in rex.keys():
                    jbody['category']=rex['category']
                if options.removemessagedate:
                    msg,adate=splitTime(jbody['summary'])
                    jbody['summary']=msg
                es=pyes.ES(("http",options.esserver,options.esport))
                res=es.index(index='alerts',doc_type='alert',doc=jbody)
                ch.basic_publish(exchange=options.alertexchange,routing_key=options.alertqueue,body=json.dumps(jbody))
                break #only publish once on the first regex hit
    except Exception as e:
        logger.error('Exception on event callback looking for alerts: {0}'.format(e))


def main():
    if options.output=='syslog':    
        logger.addHandler(SysLogHandler(address=(options.sysloghostname,options.syslogport)))
    else:
        sh=logging.StreamHandler(sys.stderr)
        sh.setFormatter(formatter)
        logger.addHandler(sh)
        
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=options.mqserver))
    channel = connection.channel()
    
    #declare the exchanges
    channel.exchange_declare(exchange=options.alertexchange,type='topic')
    
    channel.exchange_declare(exchange=options.eventexchange,type='topic')
    result = channel.queue_declare(exclusive=False)
    queue_name = result.method.queue
    channel.queue_bind(exchange='events', queue=queue_name,routing_key=options.eventqueue)
    
    #channel.basic_qos(prefetch_count=1)
    channel.basic_consume(callback,queue=queue_name,no_ack=True)
    print ' [*] Ready for messages.'
    channel.start_consuming()



def initConfig():
    #change this to your default zone for when it's not specified
    options.mqserver=getConfig('mqserver','localhost',options.configfile)               #message queue server hostname
    options.eventqueue=getConfig('eventqueue','mozdef.event',options.configfile)       #event queue topic
    options.eventexchange=getConfig('eventexchange','events',options.configfile)        #event queue exchange name
    options.alertqueue=getConfig('alertqueue','mozdef.alert',options.configfile)        #alert queue topic
    options.alertexchange=getConfig('alertexchange','alerts',options.configfile)        #alert queue exchange name
    #options.esserver=getConfig('esserver','localhost',options.configfile)
    #options.esport=getConfig('esport',9200,options.configfile)
    options.output=getConfig('output','stdout',options.configfile)                      #output our log to stdout or syslog
    options.sysloghostname=getConfig('sysloghostname','localhost',options.configfile)   #syslog hostname
    options.syslogport=getConfig('syslogport',514,options.configfile)                   #syslog port
    options.removemessagedate=getConfig('removemessagedate',True,options.configfile)    #do we remove any date string from the 'summary' field (removes syslog timestamps)
    options.esserver=getConfig('esserver','localhost',options.configfile)
    options.esport=getConfig('esport',9200,options.configfile)
    
    #load any alert regexes from the config file
    #expecting one line, tab delimited json:
    #regexes={"type":"LDAP Group Update","expression":"ou=groups","severity":"INFO"}   {"type":"LDAP Delete","expression":"delete","severity":"INFO"}
    #adding a tag attribute will limit expression matching to items with that tag
    #qregexes={"type":"LDAP Group Update","expression":"ou=groups","severity":"INFO","tag":"ldap"}
    regexes=getConfig('regexes','',options.configfile)
    options.regexlist=[]
    if len(regexes)>0:
        for r in regexes.split('\t'):
            options.regexlist.append(json.loads(r))
    
if __name__ == '__main__':
    parser=OptionParser()
    parser.add_option("-c", dest='configfile' , default='alertWorker.conf', help="configuration file to use")
    (options,args) = parser.parse_args()
    initConfig()
    main()
