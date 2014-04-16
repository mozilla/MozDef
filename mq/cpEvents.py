#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
# Copyright (c) 2014 Mozilla Corporation
#
# Contributors:
# Jeff Bryner jbryner@mozilla.com

import os
import sys
import pyes
from kombu import Connection,Queue,Exchange
from kombu.mixins import ConsumerMixin
from configlib import getConfig,OptionParser

def esConnect():
    '''open or re-open a connection to elastic search'''
    return pyes.ES((list('{0}'.format(s) for s in options.esservers)))
    
class eventConsumer(ConsumerMixin):
    '''kombu mixin to receive events and copy them to an elastic search server.
       Helpful when testing new clusters, for failover,etc.
       Does not ack messages, deletes queues on exit so not guaranteed to copy all messages
    '''
    def __init__(self, mqConnection,eventQueue,eventExchange,esConnection):
        self.connection = mqConnection
        self.esConnection=esConnection
        self.eventQueue=eventQueue
        self.eventExchange=eventExchange

    def get_consumers(self, Consumer, channel):
        consumer=Consumer(self.eventQueue, no_ack=True,callbacks=[self.on_message], accept=['json'])
        consumer.qos(prefetch_count=options.prefetch)
        return [consumer]

    def on_message(self, body, message):
        try:
            print("RECEIVED MESSAGE: %r" % (body, ))
            #copy event to es cluster
            try:
                res=self.esConnection.index(index='events',doc_type='event',doc=body)
            #handle loss of server or race condition with index rotation/creation/aliasing
            except (pyes.exceptions.NoServerAvailable,pyes.exceptions.InvalidIndexNameException) as e:
                pass    
        except Exception as e:
            sys.stderr.write("exception in events queue %r\n"%e)

def main():    
    #connect and declare the message queue/kombu objects.
    connString='amqp://{0}:{1}@{2}:{3}//'.format(options.mquser,options.mqpassword,options.mqserver,options.mqport)
    mqConn=Connection(connString)
    
    #topic exchange for listening to mozdef.event
    eventExchange=Exchange(name=options.eventexchange,type='topic',durable=False,delivery_mode=1)
    eventExchange(mqConn).declare()
    #Queue for the exchange
    eventQueue=Queue('',exchange=eventExchange,routing_key=options.routingkey,durable=False,exclusive=True,auto_delete=True)
    #eventQueue(mqConn).declare()
    
    #consume our queue and publish on the topic exchange
    eventConsumer(mqConn,eventQueue,eventExchange,es).run()
    

def initConfig():
    options.mqserver=getConfig('mqserver','localhost',options.configfile)
    options.eventexchange=getConfig('eventexchange','events',options.configfile)
    options.routingkey=getConfig('routingkey','mozdef.event',options.configfile)
    options.esservers=list(getConfig('esservers','http://localhost:9200',options.configfile).split(','))
    #how many messages to ask for at once.
    options.prefetch=getConfig('prefetch',1,options.configfile)
    options.mquser=getConfig('mquser','guest',options.configfile)
    options.mqpassword=getConfig('mqpassword','guest',options.configfile)
    options.mqport=getConfig('mqport',5672,options.configfile)    

if __name__ == '__main__':
    parser=OptionParser()
    parser.add_option("-c", dest='configfile' , default=sys.argv[0].replace('.py','.conf'), help="configuration file to use")
    (options,args) = parser.parse_args()
    initConfig()
    #open ES connection globally so we don't waste time opening it per message
    es=esConnect()
    main()