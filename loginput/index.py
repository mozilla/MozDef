# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
# Copyright (c) 2017 Mozilla Corporation
#
# Contributors:
# Jeff Bryner jbryner@mozilla.com
# Brandon Myers bmyers@mozilla.com

import os
import sys
import bottle
from bottle import debug,route, run, template, response,request,post, default_app
from bottle import _stdout as bottlelog
import kombu
from kombu import Connection,Queue,Exchange
import json
from configlib import getConfig,OptionParser


@route('/status')
@route('/status/')
def status():
    '''endpoint for a status/health check'''
    if request.body:
        request.body.read()
        request.body.close()
    response.status = 200
    response.content_type = "application/json"
    response.body = json.dumps(dict(status='ok'))
    return response

@route('/test')
@route('/test/')
def testindex():
    ip = request.environ.get('REMOTE_ADDR')
    #response.headers['X-IP'] = '{0}'.format(ip)
    response.status=200

#act like elastic search bulk index
@route('/_bulk',method='POST')
@route('/_bulk/',method='POST')
def bulkindex():
    if request.body:
        bulkpost=request.body.read()
        #bottlelog('request:{0}\n'.format(bulkpost))
        request.body.close()
        if len(bulkpost)>10: #TODO Check for bulk format.
            #iterate on messages and post to event message queue

            eventlist=[]
            for i in bulkpost.splitlines():
                eventlist.append(i)

            for i in eventlist:
                try:
                    #valid json?
                    try:
                        eventDict=json.loads(i)
                    except ValueError as e:
                        response.status=500
                        return
                    if not 'index' in json.loads(i).keys(): #don't post the items telling us where to post things..
                        ensurePublish=mqConn.ensure(mqproducer,mqproducer.publish,max_retries=10)
                        ensurePublish(eventDict,exchange=eventTaskExchange,routing_key=options.taskexchange)
                except ValueError:
                    bottlelog('value error {0}'.format(i))
    return

@route('/_status')
@route('/_status/')
@route('/nxlog/', method=['POST','PUT'])
@route('/nxlog',  method=['POST','PUT'])
@route('/events/',method=['POST','PUT'])
@route('/events', method=['POST','PUT'])
def eventsindex():
    if request.body:
        anevent=request.body.read()
        #bottlelog('request:{0}\n'.format(anevent))
        request.body.close()
        #valid json?
        try:
            eventDict=json.loads(anevent)
        except ValueError as e:
            response.status=500
            return
        #let the message queue worker who gets this know where it was posted
        eventDict['endpoint']='events'
        #post to event message queue
        ensurePublish=mqConn.ensure(mqproducer,mqproducer.publish,max_retries=10)
        ensurePublish(eventDict,exchange=eventTaskExchange,routing_key=options.taskexchange)

    return

@route('/cef', method=['POST','PUT'])
@route('/cef/',method=['POST','PUT'])
#debug(True)
def cefindex():
    if request.body:
        anevent=request.body.read()
        request.body.close()
        #valid json?
        try:
            cefDict=json.loads(anevent)
        except ValueError as e:
            response.status=500
            return
        #let the message queue worker who gets this know where it was posted
        cefDict['endpoint']='cef'

        #post to eventtask exchange
        ensurePublish=mqConn.ensure(mqproducer,mqproducer.publish,max_retries=10)
        ensurePublish(cefDict,exchange=eventTaskExchange,routing_key=options.taskexchange)
    return

@route('/custom/<application>',method=['POST','PUT'])
def customindex(application):
    '''
        and endpoint designed for custom applications that want to post data
        to elastic search through the mozdef event interface
        post to /custom/vulnerabilities
        for example to post vulnerability in a custom format
        Posts must be in json and are best formatted using a plugin
        to the esworker.py process.
    '''
    if request.body:
        anevent=request.body.read()
        request.body.close()
        #valid json?
        try:
            customDict=json.loads(anevent)
        except ValueError as e:
            response.status=500
            return
        #let the message queue worker who gets this know where it was posted
        customDict['endpoint']= application
        customDict['customendpoint'] = True

        #post to eventtask exchange
        ensurePublish=mqConn.ensure(mqproducer,mqproducer.publish,max_retries=10)
        ensurePublish(customDict,exchange=eventTaskExchange,routing_key=options.taskexchange)
    return


def initConfig():
    options.mqserver=getConfig('mqserver','localhost',options.configfile)
    options.taskexchange=getConfig('taskexchange','eventtask',options.configfile)
    options.mquser=getConfig('mquser','guest',options.configfile)
    options.mqpassword=getConfig('mqpassword','guest',options.configfile)
    options.mqport=getConfig('mqport',5672,options.configfile)


#get config info:
parser=OptionParser()
parser.add_option("-c", dest='configfile' , default=os.path.join(os.path.dirname(__file__), __file__).replace('.py', '.conf'), help="configuration file to use")
(options,args) = parser.parse_args()
initConfig()

#connect and declare the message queue/kombu objects.
connString='amqp://{0}:{1}@{2}:{3}//'.format(options.mquser,options.mqpassword,options.mqserver,options.mqport)
mqConn=Connection(connString)

eventTaskExchange=Exchange(name=options.taskexchange,type='direct',durable=True)
eventTaskExchange(mqConn).declare()
eventTaskQueue=Queue(options.taskexchange,exchange=eventTaskExchange)
eventTaskQueue(mqConn).declare()
mqproducer = mqConn.Producer(serializer='json')

if __name__ == "__main__":
    run(host="0.0.0.0", port=8080)
else:
    application = default_app()
