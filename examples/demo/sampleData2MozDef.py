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
from configlib import getConfig, OptionParser, setConfig
import glob
from datetime import datetime
from datetime import timedelta
from dateutil.parser import parse
from datetime import date
import pytz

#use futures to run in the background
#httpsession = FuturesSession(max_workers=5)
httpsession = requests.session()
httpsession.trust_env=False #turns of needless .netrc check for creds
#a = requests.adapters.HTTPAdapter(max_retries=2)
#httpsession.mount('http://', a)



logger = logging.getLogger(sys.argv[0])
logger.level=logging.INFO

formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

#create a list of logs we can append json to and call for a post when we want.
logcache=Queue()


def toUTC(suspectedDate,localTimeZone=None):
    '''make a UTC date out of almost anything'''
    utc=pytz.UTC
    objDate=None
    if localTimeZone is None:
        localTimeZone=options.defaulttimezone
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

    return objDate


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
                print(r, postdata)
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
    #random, IPs
    return '.'.join("%d" % (random.randint(0,254)) for x in range(4))
    
def genAttackerIPv4():
    #random, but not too random as to allow for alerting about attacks from
    #the same IP.
    coreIPs=['1.93.25.',
             '222.73.115.',
             '116.10.191.',
             '144.0.0.']
    #change this to non zero according to taste for semi-random-ness 
    if random.randint(0,10)>= 0:
        return '{0}{1}'.format(random.choice(coreIPs), random.randint(1,2))
    else:
        return '.'.join("%d" % (random.randint(0,254)) for x in range(4))
    

def makeEvents():
    try:
        eventfiles = glob.glob(options.eventsglob)
        #pick a random number of events to send
        for i in range(1, random.randrange(20, 100)):
            #pick a random type of event to send
            eventfile = random.choice(eventfiles)
            #print(eventfile)
            events = json.load(open(eventfile))
            target = random.randint(0, len(events))
            for event in events[target:target+1]:
                event['timestamp'] = pytz.timezone('UTC').localize(datetime.utcnow()).isoformat()
                #remove stored times
                if 'utctimestamp' in event.keys():
                    del event['utctimestamp']
                if 'receivedtimestamp' in event.keys():
                    del event['receivedtimestamp']
                
                #add demo to the tags so it's clear it's not real data.
                if 'tags' not in event.keys():
                    event['tags'] = list()
                
                event['tags'].append('demodata')
                
                #replace potential <randomipaddress> with a random ip address
                if 'summary' in event.keys() and '<randomipaddress>' in event['summary']:
                    randomIP = genRandomIPv4()
                    event['summary'] = event['summary'].replace("<randomipaddress>", randomIP)
                    if 'details' not in event.keys():
                        event['details'] = dict()
                    event['details']['sourceipaddress'] = randomIP
                    event['details']['sourceipv4address'] = randomIP                        

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

def makeAlerts():
    '''
    send events that will be correlated into alerts
    '''
    try:
        #time for us to run?
        timetoRun=toUTC(options.lastalert) + timedelta(minutes=options.alertsminutesinterval)
        if timetoRun > toUTC(datetime.now()):
            #print(timetoRun)
            return
        
        #print(timetoRun, options.lastalert)
        eventfiles = glob.glob(options.alertsglob)
        #pick a random number of events to send
        for i in range(0, options.alertscount):
            #pick a random type of event to send
            eventfile = random.choice(eventfiles)
            events = json.load(open(eventfile))
            target = random.randint(0, len(events))
            # if there's only one event in the file..use it.
            if len(events) == 1 and target == 1:
                target = 0
            for event in events[target:target+1]:
                event['timestamp'] = pytz.timezone('UTC').localize(datetime.utcnow()).isoformat()
                #remove stored times
                if 'utctimestamp' in event.keys():
                    del event['utctimestamp']
                if 'receivedtimestamp' in event.keys():
                    del event['receivedtimestamp']
                
                #add demo to the tags so it's clear it's not real data.
                if 'tags' not in event.keys():
                    event['tags'] = list()
                
                event['tags'].append('demodata')
                event['tags'].append('demoalert')
                
                #replace potential <randomipaddress> with a random ip address
                if 'summary' in event.keys() and '<randomipaddress>' in event['summary']:
                    randomIP = genRandomIPv4()
                    event['summary'] = event['summary'].replace("<randomipaddress>", randomIP)
                    if 'details' not in event.keys():
                        event['details'] = dict()
                    event['details']['sourceipaddress'] = randomIP
                    event['details']['sourceipv4address'] = randomIP

                if 'duplicate' in event.keys():
                    # send this event multiple times to trigger an alert
                    for x in range(0, int(event['duplicate'])):
                        logcache.put(json.dumps(event))
                else:
                    logcache.put(json.dumps(event))
            lastalert=toUTC(datetime.now()).isoformat()
            setConfig('lastalert',lastalert,options.configfile)
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
            
def makeAttackers():
    '''
    send events that will be correlated into attackers using pre-defined IPs
    '''
    try:
        #time for us to run?
        timetoRun=toUTC(options.lastattacker) + timedelta(minutes=options.attackersminutesinterval)
        if timetoRun > toUTC(datetime.now()):
            #print(timetoRun)
            return
        
        #print(timetoRun, options.lastalert)
        eventfiles = glob.glob(options.alertsglob)
        #pick a random number of events to send
        for i in range(0, options.alertscount):
            #pick a random type of event to send
            eventfile = random.choice(eventfiles)
            events = json.load(open(eventfile))
            target = random.randint(0, len(events))
            # if there's only one event in the file..use it.
            if len(events) == 1 and target == 1:
                target = 0
            for event in events[target:target+1]:
                event['timestamp'] = pytz.timezone('UTC').localize(datetime.utcnow()).isoformat()
                #remove stored times
                if 'utctimestamp' in event.keys():
                    del event['utctimestamp']
                if 'receivedtimestamp' in event.keys():
                    del event['receivedtimestamp']
                
                #add demo to the tags so it's clear it's not real data.
                if 'tags' not in event.keys():
                    event['tags'] = list()
                
                event['tags'].append('demodata')
                event['tags'].append('demoalert')
                
                #replace potential <randomipaddress> with a random ip address
                if 'summary' in event.keys() and '<randomipaddress>' in event['summary']:
                    randomIP = genAttackerIPv4()
                    event['summary'] = event['summary'].replace("<randomipaddress>", randomIP)
                    if 'details' not in event.keys():
                        event['details'] = dict()
                    event['details']['sourceipaddress'] = randomIP
                    event['details']['sourceipv4address'] = randomIP

                if 'duplicate' in event.keys():
                    # send this event multiple times to trigger an alert
                    for x in range(0, int(event['duplicate'])):
                        logcache.put(json.dumps(event))
                else:
                    logcache.put(json.dumps(event))
            lastattacker=toUTC(datetime.now()).isoformat()
            setConfig('lastattacker',lastattacker,options.configfile)
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
    options.defaulttimezone=getConfig('defaulttimezone','UTC',options.configfile)
    options.url = getConfig('url', 'http://localhost:8080/events/', options.configfile)
    options.eventsglob = getConfig('eventsglob', './sampleevents/events*json', options.configfile)
    options.alertsglob = getConfig('alertsglob', './sampleevents/alert*json', options.configfile)
    options.attackersglob = getConfig('attackersglob', './sampleevents/attacker*json', options.configfile)
    #how many alerts to create
    options.alertscount = getConfig('alertscount', 2, options.configfile)
    #how many minutes to wait between creating ^ alerts 
    options.alertsminutesinterval = getConfig('alertsminutesinterval', 5, options.configfile)
    options.lastalert = getConfig('lastalert', datetime.now() - timedelta(hours=1), options.configfile)
    
    #how many attackers to create
    options.attackerscount = getConfig('attackers', 1, options.configfile)
    #how many minutes to wait between creating ^ attackers 
    options.attackersminutesinterval = getConfig('attackersminutesinterval', 5, options.configfile)
    options.lastattacker = getConfig('lastattacker', datetime.now() - timedelta(hours=1), options.configfile)


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
    
    makeEvents()
    makeAlerts()
    makeAttackers()
    

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
