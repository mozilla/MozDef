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
from optparse import OptionParser
from requests_futures.sessions import FuturesSession
from multiprocessing import Process, Queue
import random
import logging
from logging.handlers import SysLogHandler
from Queue import Empty
from  requests.packages.urllib3.exceptions import ClosedPoolError
import requests
import time

httpsession = FuturesSession(max_workers=5)
httpsession.trust_env=False #turns of needless .netrc check for creds
#a = requests.adapters.HTTPAdapter(max_retries=2)
#httpsession.mount('http://', a)



logger = logging.getLogger(sys.argv[0])
logger.level=logging.DEBUG

formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
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
                posts.append((r,postdata,url))
    except Empty as e:
        pass
    for p,postdata,url in posts:
        try:
            if p.result().status_code >=500:
                logger.error("exception posting to %s %r [will retry]\n"%(url,p.result().status_code))
                #try again later when the next message in forces other attempts at posting.
                logcache.put(postdata)
        except ClosedPoolError as e:
            #logger.fatal("Closed Pool Error exception posting to %s %r %r [will retry]\n"%(url,e,postdata))
            logcache.put(postdata)
        except Exception as e:
            logger.fatal("exception posting to %s %r %r [will not retry]\n"%(url,e,postdata))
            sys.exit(1)

if __name__ == '__main__':
    parser=OptionParser()
    parser.add_option("-u", dest='url' , default='http://localhost:8080/events/', help="mozdef events URL to use when posting events")
    (options,args) = parser.parse_args()
    sh=logging.StreamHandler(sys.stdout)
    sh.setFormatter(formatter)
    logger.addHandler(sh)
    #create a list of logs we can append json to and call for a post when we want.
    logcache=Queue()
    try:
        for i in range(0,10):

            print(i)
            alog=dict(eventtime=pytz.timezone('US/Pacific').localize(datetime.now()).isoformat(),\
                        hostname=socket.gethostname(),\
                        processid=os.getpid(),\
                        processname=sys.argv[0],\
                        severity='INFO',\
                        summary='joe login failed',\
                        category='authentication',\
                        tags=[],\
                        details=[])
            alog['details']=dict(success=True,username='mozdef')
            alog['tags']=['mozdef','stresstest']

            logcache.put(json.dumps(alog))
            if not logcache.empty():
                time.sleep(.001)
                try:
                    postingProcess=Process(target=postLogs,args=(logcache,),name="json2MozdefStressTest")
                    postingProcess.start()
                except OSError as e:
                    if e.errno==35: #resource temporarily unavailable.
                        print(e)
                        pass
                    else:
                        logger.error('%r'%e)

        while not logcache.empty():
            try:
                postingProcess=Process(target=postLogs,args=(logcache,),name="json2MozdefStressTest")
                postingProcess.start()
            except OSError as e:
                if e.errno==35: #resource temporarily unavailable.
                    print(e)
                    pass
                else:
                    logger.error('%r'%e)
    except KeyboardInterrupt as e:
        sys.exit(1)
