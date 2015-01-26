#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
# Copyright (c) 2014 Mozilla Corporation
#
# Contributors:
# Anthony Verez averez@mozilla.com
# Julien Vehent jvehent@mozilla.com

import os
import sys
from configlib import getConfig,OptionParser,setConfig
import logging
from logging.handlers import SysLogHandler
import gzip
from StringIO import StringIO
import json
import time
import pyes
from datetime import datetime
from datetime import timedelta
from dateutil.parser import parse
from datetime import date
import pytz
import requests
import pprint as pp
import hashlib
import gnupg
import random

logger = logging.getLogger(sys.argv[0])
logger.level=logging.INFO
formatter = logging.Formatter('%(asctime)s %(name)s %(levelname)s %(message)s')

def makeToken(gpghome, keyid):
    gpg = gnupg.GPG(gnupghome=gpghome)
    version = "1"
    timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    nonce = str(random.randint(10000, 18446744073709551616))
    token = version + ";" + timestamp + ";" + nonce
    sig = gpg.sign(token + "\n",
        keyid=keyid,
        detach=True, clearsign=True)
    token += ";"
    linectr=0
    for line in iter(str(sig).splitlines()):
        linectr+=1
        if linectr < 4 or line.startswith('-') or not line:
            continue
        token += line
    return token

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

    return objDate

def main():
    if options.output=='syslog':
        logger.addHandler(SysLogHandler(address=(options.sysloghostname,options.syslogport)))
    else:
        sh=logging.StreamHandler(sys.stderr)
        sh.setFormatter(formatter)
        logger.addHandler(sh)

    logger.debug('started')
    logger.debug(options)
    try:
        es=pyes.ES((list('{0}'.format(s) for s in options.esservers)))
        #capture the time we start running so next time we catch any files created while we run.
        lastrun=str(options.lastrun.isoformat())
        today=datetime.utcnow().isoformat()+'+00:00'
        # set the max num of items to 50k. At 600kB per item, that's already ~30MB of json body.
        url = options.mighost+'/api/v1/search?type=command&status=success&threatfamily=compliance&report=complianceitems&limit=50000&before='+today+'&after='+lastrun
        url = url.replace('+00:00', 'Z')

        # Prepare the request, make an authorization token using the local keyring
        token = makeToken(options.gpghome, options.keyid)
        r = requests.get(url,
            headers={'X-PGPAUTHORIZATION': token},
            timeout=240, # timeout at 4 minutes. those are big requests.
            verify=True)
        if r.status_code == 200:
            migjson=r.json()
            logger.debug(url)
            cicnt=0
            for items in migjson['collection']['items']:
                for dataitem in items['data']:
                    if dataitem['name'] == 'compliance item':
                        cicnt += 1
                        complianceitem = dataitem['value']
                        # historical data - index the new logs
                        res=es.index(index='complianceitems',doc_type='history',doc=complianceitem)
                        # last_known_state data - update the logs
                        # _id = md5('complianceitems'+check.ref+check.test.value+target)
                        docid=hashlib.md5('complianceitems'+complianceitem['check']['ref']+complianceitem['check']['test']['value']+complianceitem['target']).hexdigest()
                        res=es.index(index='complianceitems',id=docid,doc_type='last_known_state',doc=complianceitem)
            if cicnt == 0:
                logger.debug("No compliance item available, terminating")
            setConfig('lastrun',today,options.configfile)
        elif r.status_code == 500:
            # api returns a 500 with an error body on failures
            migjson=r.json()
            raise Exception("API returned HTTP code %s and error '%s:%s'" %
                                (r.status_code,
                                migjson['collection']['error']['code'],
                                migjson['collection']['error']['message'])
                            )
        else:
            # another type of failure that's unlikely to have an error body
            raise Exception("Failed with HTTP code %s" % r.status_code)
    except Exception as e:
        logger.error("Unhandled exception, terminating: %r"%e)


def initConfig():
    options.output=getConfig('output','stdout',options.configfile)                      #output our log to stdout or syslog
    options.sysloghostname=getConfig('sysloghostname','localhost',options.configfile)   #syslog hostname
    options.syslogport=getConfig('syslogport',514,options.configfile)                   #syslog port
    options.defaultTimeZone=getConfig('defaulttimezone','US/Pacific',options.configfile)
    # Z = UTC, -07:00 = PDT
    options.mighost=getConfig('mighost','https://localhost',options.configfile)
    options.gpghome=getConfig('gpghome','/home/someuser/.gnupg',options.configfile)
    options.keyid=getConfig('keyid','E60892BB9BD89A69F759A1A0A3D652173B763E8F',options.configfile)
    options.esservers=list(getConfig('esservers','http://localhost:9200',options.configfile).split(','))
    options.lastrun=toUTC(getConfig('lastrun',toUTC(datetime.now()-timedelta(minutes=15)),options.configfile))

if __name__ == '__main__':
    parser=OptionParser()
    parser.add_option("-c", dest='configfile' , default=sys.argv[0].replace('.py', '.conf'), help="configuration file to use")
    (options,args) = parser.parse_args()
    initConfig()
    main()
