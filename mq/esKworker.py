#!/usr/bin/env python
import time
import pyes
from datetime import datetime
from dateutil.parser import parse
import pytz
import sys
import json
from configlib import getConfig,OptionParser
from kombu import Connection,Queue
from kombu.mixins import ConsumerMixin

def toUTC(suspectedDate,localTimeZone=None):
    '''make a UTC date out of almost anything'''
    utc=pytz.UTC
    objDate=None
    if localTimeZone is None:
        localTimeZone=options.defaultTimeZone
    if type(suspectedDate) in (str,unicode):
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
        
    return objDate.isoformat()

def removeDictAt(aDict):
    '''remove the @ symbol from any field/key names'''
    returndict=dict()
    for k,v in aDict.iteritems():
        k=k.replace('@','')
        returndict[k]=v
    return returndict

def removeAt(astring):
    '''remove the leading @ from a string'''
    return astring.replace('@','')

def isCEF(aDict):
    #determine if this is a CEF event
    #could be an event posted to the /cef http endpoint
    if 'endpoint' in aDict.keys() and aDict['endpoint']=='cef':
        return True
    #maybe it snuck in some other way
    #check some key CEF indicators (the header fields)
    if 'fields' in aDict.keys():
    
        lowerKeys=[s.lower() for s in aDict['fields'].keys()]
        if 'devicevendor' in lowerKeys and 'deviceproduct' in lowerKeys and 'deviceversion' in lowerKeys:
            return True
    return False

def keyMapping(aDict):
    '''map common key/fields to a normalized structure,
       explicitly typed when possible to avoid schema changes for upsteam consumers
       Special accomodations made for logstash,nxlog, beaver, heka and CEF
       Some shippers attempt to conform to logstash-style @fieldname convention.
       This strips the leading at symbol since it breaks some elastic search libraries like elasticutils.
    '''
    returndict=dict()
    #save the source event for chain of custody/forensics
    #returndict['original']=aDict
    
    for k,v in aDict.iteritems():
        
        if removeAt(k.lower()) in ('message','summary'):
            returndict[u'summary']=str(v)
            
        if removeAt(k.lower()) in ('eventtime','timestamp'):
            returndict[u'utctimestamp']=toUTC(v)
            returndict[u'timestamp']=parse(v,fuzzy=True).isoformat()
            
        if removeAt(k.lower()) in ('hostname','source_host','host'):
            returndict[u'hostname']=str(v)
        

        if removeAt(k.lower()) in ('tags'):
            if len(v)>0:
                returndict[u'tags']=v

        #nxlog keeps the severity name in syslogseverity,everyone else should use severity or level.
        if removeAt(k.lower()) in ('syslogseverity','severity','severityvalue','level'):
            returndict[u'severity']=str(v).upper()
            
        if removeAt(k.lower()) in ('facility','syslogfacility'):
            returndict[u'facility']=str(v)

        if removeAt(k.lower()) in ('pid','processid'):
            returndict[u'processid']=str(v)
        
        #nxlog sets sourcename to the processname (i.e. sshd), everyone else should call it process name or pname
        if removeAt(k.lower()) in ('pname','processname','sourcename'):
            returndict[u'processname']=str(v)
        
        #the file, or source
        if removeAt(k.lower()) in ('path','logger','file'):
            returndict[u'eventsource']=str(v)

        if removeAt(k.lower()) in ('type','eventtype','category'):
            returndict[u'eventtype']=str(v)

        #custom fields as a list/array
        if removeAt(k.lower()) in ('fields','details'):
            if len(v)>0:
                returndict[u'details']=v
        
        #custom fields/details as a one off, not in an array fields.something=value or details.something=value
        if removeAt(k.lower()).startswith('fields.') or removeAt(k.lower()).startswith('details.'):
            #custom/parsed field
            returndict[unicode(k.lower().replace('fields','details'))]=str(v)
    
    if 'utctimestamp' not in returndict.keys():
        #we didn't find a reasonable timestamp, so lets set it to now:
        returndict['utctimestamp']=toUTC(datetime.now())
    
    #set the timestamp when we received it, i.e. now
    returndict['receivedtimestatmp']=toUTC(datetime.now())
    

    return returndict
        
def normaliseJSON(jsonStringIn):
    try:
        j=json.loads(jsonStringIn)
        j=keyMapping(j)
        return j
        
    except ValueError as ve:
        sys.stderr.write("Invalid json %r\n"%jsonStringIn)
        return None
    except Exception as e:
        sys.stderr.write("Exception normalizing json %r\n"%e)
        return None

def callback(ch, method, properties, body):
    #print(" [*] Received %r" % (body))
    #declare elastic search connection
    #es=pyes.ES(("http",options.esserver,options.esport))
    #es=pyes.ES((list('{0}'.format(s) for s in options.esservers)))
    try:
        bodydict=json.loads(body)   #raw body we were sent
        jbody=normaliseJSON(body)   #normalized body with validated fields to be sent to elastic search
        
        if jbody is not None:       #could be empty,or invalid
            jbody=json.JSONEncoder().encode(jbody)
            
            #figure out what type of document we are indexing and post to the elastic search index.
            doctype='event'
            if isCEF(bodydict):
                #cef records are set to the 'deviceproduct' field value.
                doctype='cef'
                if 'deviceproduct' in bodydict['fields'].keys():
                    doctype=bodydict['fields']['deviceproduct']
            
            res=es.index(index='events',doc_type=doctype,doc=jbody)
            #print(' [*] elasticsearch:{0}'.format(res))
            #publish on the events topic queue
            ch.basic_publish(exchange='events',routing_key='mozdef.event',body=jbody)  
    
        ch.basic_ack(delivery_tag = method.delivery_tag)
    except Exception as e:
        sys.stderr.write("esworker exception in events queue %r\n"%e)

class kConsumer(ConsumerMixin):

    def __init__(self, mqconnection,queue,esconnection):
        self.connection = mqconnection
        self.esconnection=esconnection
        self.queue=queue

    def get_consumers(self, Consumer, channel):
        return [
            Consumer(self.queue, callbacks=[self.on_message], accept=['json']),
        ]

    def on_message(self, body, message):
        #print("RECEIVED MESSAGE: %r" % (body, ))
        try:
            if isinstance(body,dict):
                bodydict=body
                jbody=normaliseJSON(json.dumps(body))
            elif isinstance(body,str):
                bodydict=json.loads(body)   #raw body we were sent
                jbody=normaliseJSON(body)   #normalized body with validated fields to be sent to elastic search
            else:
                sys.stderr.write("esworker exception: unknown body type received %r\n"%body)
                
            if jbody is not None:       #could be empty,or invalid
                jbody=json.JSONEncoder().encode(jbody)
                
                #figure out what type of document we are indexing and post to the elastic search index.
                doctype='event'
                if isCEF(bodydict):
                    #cef records are set to the 'deviceproduct' field value.
                    doctype='cef'
                    if 'deviceproduct' in bodydict['fields'].keys():
                        doctype=bodydict['fields']['deviceproduct']
                
                res=self.esconnection.index(index='events',doc_type=doctype,doc=jbody)
                #print(' [*] elasticsearch:{0}'.format(res))
                #TODO publish on the events topic queue
        
            message.ack()
        except OSError as e:
            sys.stderr.write("esworker exception in events queue %r\n"%e)


def main():
    
    #connect and declare the queues
    connString='amqp://guest:guest@{0}:5672//'.format(options.mqserver)
    mqConn=Connection(connString)
    eventTaskQueue=Queue(options.taskqueue)
    eventTaskQueue(mqConn).declare()
    kConsumer(mqConn,eventTaskQueue,es).run()
    

def initConfig():
    #change this to your default zone for when it's not specified
    options.defaultTimeZone=getConfig('defaulttimezone','UTC',options.configfile)
    
    options.mqserver=getConfig('mqserver','localhost',options.configfile)
    options.taskqueue=getConfig('taskqueue','eventtask',options.configfile)
    #options.esserver=getConfig('esserver','localhost',options.configfile)
    options.esservers=list(getConfig('esservers','http://localhost:9200',options.configfile).split(','))
    #how many messages to ask for at once.
    options.prefetch=getConfig('prefetch',50,options.configfile)

if __name__ == '__main__':
    parser=OptionParser()
    parser.add_option("-c", dest='configfile' , default=sys.argv[0].replace('.py','.conf'), help="configuration file to use")
    (options,args) = parser.parse_args()
    initConfig()
    #open ES connection globally so we don't waste time opening it per message
    es=pyes.ES((list('{0}'.format(s) for s in options.esservers)))
    main()