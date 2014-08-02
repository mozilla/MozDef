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
from datetime import datetime
import pytz
import json
import socket
import json
from requests_futures.sessions import FuturesSession
from multiprocessing import Process, Queue
import random
import logging
from logging.handlers import SysLogHandler
from Queue import Empty
from  requests.packages.urllib3.exceptions import ClosedPoolError
import requests
import time
from configlib import getConfig, OptionParser
import glob

#use futures to run in the background
#httpsession = FuturesSession(max_workers=5)
httpsession = requests.session()
httpsession.trust_env=False #turns of needless .netrc check for creds
#a = requests.adapters.HTTPAdapter(max_retries=2)
#httpsession.mount('http://', a)



logger = logging.getLogger(sys.argv[0])
logger.level=logging.DEBUG

formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

#create a list of logs we can append json to and call for a post when we want.
logcache=Queue()

def postLogs(logcache):
    #post logs asynchronously with requests workers and check on the results
    #expects a queue object from the multiprocessing library
    posts=[]
    try:
        while not logcache.empty():
            postdata=logcache.get_nowait()
            if len(postdata)>0:
                url=options.url
                a=httpsession.get_adapter(url)
                a.max_retries=3
                r=httpsession.post(url,data=postdata)
                #print(r, postdata)
                #append to posts if this is long running and you want
                #events to try again later.
                #posts.append((r,postdata,url))
    except Empty as e:
        pass
    #for p,postdata,url in posts:
        #try:
            #if p.result().status_code >=500:
                #logger.error("exception posting to %s %r [will retry]\n"%(url,p.result().status_code))
                ##try again later when the next message in forces other attempts at posting.
                #logcache.put(postdata)
        #except ClosedPoolError as e:
            ##logger.fatal("Closed Pool Error exception posting to %s %r %r [will retry]\n"%(url,e,postdata))
            #logcache.put(postdata)
        #except Exception as e:
            #logger.fatal("exception posting to %s %r %r [will not retry]\n"%(url,e,postdata))
            #sys.exit(1)

def genRandomIPv4():
    #random, but not too random as to allow for alerting about attacks from
    #the same IP.
    coreIPs=['1.93.25.',
             '222.73.115.',
             '116.10.191.',
             '144.0.0.']
    if random.randint(0,10)>=5:
        return '{0}{1}'.format(random.choice(coreIPs), random.randint(1,2))
    else:
        return '.'.join("%d" % (random.randint(0,254)) for x in range(4))

def makeLogs():
    try:
        eventfiles = glob.glob(options.jsonglob)
        eventfiles = ['./sampleevents/events-event.json']
        #pick a random number of events to send
        for i in range(0, random.randrange(0, 200)):
            #pick a random type of event to send
            eventfile = random.choice(eventfiles)
            #print(eventfile)
            events = json.load(open(eventfile))
            target = random.randint(0, len(events))
            for event in events[target:target+1]:
                event['timestamp'] = pytz.timezone('UTC').localize(datetime.now()).isoformat()
                #remove stored times
                if 'utctimestamp' in event.keys():
                    del event['utctimestamp']
                if 'receivedtimestamp' in event.keys():
                    del event['receivedtimestamp']
                
                #add demo to the tags so it's clear it's not real data.
                if 'tags' not in event.keys():
                    event['tags'] = list()
                
                event['tags'].append('demodata')
                
                if 'details' in event.keys():
                    if 'sourceipaddress' in event['details']:
                        event['details']['sourceipaddress'] = genRandomIPv4()

                    if 'sourceipv4address' in event['details']:
                        event['details']['sourceipv4address'] = genRandomIPv4()                        
                    
                    if 'destinationipaddress' in event['details']:
                        event['details']['destinationipaddress'] = genRandomIPv4()
                
                    if 'destinationipv4address' in event['details']:
                        event['details']['destinationipv4address'] = genRandomIPv4()                
                
                #print(event['timestamp'], event['tags'], event['summary'])

                logcache.put(json.dumps(event))
            if not logcache.empty():
                time.sleep(.01)
                try:
                    postingProcess=Process(target=postLogs,args=(logcache,),name="json2MozdefDemoData")
                    postingProcess.start()
                except OSError as e:
                    if e.errno==35: #resource temporarily unavailable.
                        print(e)
                        pass
                    else:
                        logger.error('%r'%e)


    except KeyboardInterrupt as e:
        sys.exit(1)    

            

def initConfig():
    options.url = getConfig('url', 'http://localhost:8080/events/', options.configfile)
    options.jsonglob = getConfig('jsondir', './sampleevents/*json', options.configfile)

if __name__ == '__main__':
    parser = OptionParser()
    parser.add_option("-c",
                      dest='configfile',
                      default=sys.argv[0].replace('.py', '.conf'),
                      help="configuration file to use")
    (options, args) = parser.parse_args()
    initConfig()    
    
    sh=logging.StreamHandler(sys.stdout)
    sh.setFormatter(formatter)
    logger.addHandler(sh)
    
    makeLogs()

    while not logcache.empty():
        try:
            postingProcess=Process(target=postLogs,args=(logcache,),name="json2MozdefDemoData")
            postingProcess.start()
        except OSError as e:
            if e.errno==35: #resource temporarily unavailable.
                print(e)
                pass
            else:
                logger.error('%r'%e)
