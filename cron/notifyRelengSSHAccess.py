#!/usr/bin/env python
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Contributors:
# Jeff Bryner jbryner@mozilla.com
# Alicia Smith asmith@mozilla.com
# Brandon Myers bmyers@mozilla.com

import email.utils
import sys
import smtplib
import json
import logging
import pika
import pytz
import pyes
from collections import Counter
from configlib import getConfig, OptionParser
from datetime import datetime
from datetime import timedelta
from dateutil.parser import parse
from email.mime.text import MIMEText
from logging.handlers import SysLogHandler

logger = logging.getLogger(sys.argv[0])

def loggerTimeStamp(self, record, datefmt=None):
    return toUTC(datetime.now()).isoformat()

def initLogger():
    logger.level = logging.INFO
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    formatter.formatTime = loggerTimeStamp
    if options.output == 'syslog':
        logger.addHandler(SysLogHandler(address=(options.sysloghostname, options.syslogport)))
    else:
        sh = logging.StreamHandler(sys.stderr)
        sh.setFormatter(formatter)
        logger.addHandler(sh)

def toUTC(suspectedDate, localTimeZone="US/Pacific"):
    '''make a UTC date out of almost anything'''
    utc = pytz.UTC
    objDate = None
    if type(suspectedDate) in (str,unicode):
        objDate=parse(suspectedDate,fuzzy=True)
    elif type(suspectedDate)==datetime:
        objDate=suspectedDate

    if objDate.tzinfo is None:
        objDate = pytz.timezone(localTimeZone).localize(objDate)
        objDate = utc.normalize(objDate)
    else:
        objDate = utc.normalize(objDate)
    if objDate is not None:
        objDate = utc.normalize(objDate)

    return objDate


def esSearch(es, begindateUTC=None, enddateUTC=None):
    resultsList = list()
    if begindateUTC is None:
        begindateUTC = toUTC(datetime.now() - timedelta(hours=1))
    if enddateUTC is None:
        enddateUTC = toUTC(datetime.now())
    try:
        # search for alerts within the date range

        qType = pyes.TermFilter('category', 'access')
        qTag = pyes.TermFilter('tags', 'ssh')
        #qSev = pyes.TermFilter('severity', 'NOTICE')
        qSev = pyes.TermFilter('severity', 'notice')
        qDate = pyes.RangeQuery(qrange=pyes.ESRange('utctimestamp',
                                                    from_value=begindateUTC,
                                                    to_value=enddateUTC))

        q = pyes.ConstantScoreQuery(pyes.MatchAllQuery())

        q = pyes.FilteredQuery(q,pyes.BoolFilter(must=[qDate,
                                                       qTag,
                                                       qType,
                                                       qSev
                                                       ]))

        pyesresults = es.search(q, size=1000, indices='alerts')
        logger.debug(pyesresults.count())

        # correlate any matches
        # make a simple list of summary values that can be counted/summarized by Counter
        resultsTargets = []

        # bug in pyes..capture results as raw list or it mutates after first access:
        # copy the hits.hits list as our results, which is the same as the official elastic search library returns.
        results = pyesresults._search_raw()['hits']['hits']
        for r in results:
            # Build Up our Array
            resultsTargets.append(
                {"ts" : r['_source']['events'][0]['documentsource']['utctimestamp'],
                 "summary" : r['_source']['summary']
                }
            )

        return resultsTargets

    except pyes.exceptions.NoServerAvailable:
        logger.error('Elastic Search server could not be reached, check network connectivity')

def sendResults(summaryCounts):
    emailMessage = ''

    for i in summaryCounts:
        emailMessage += ('Timestamp: {0:4} Summary: {1:4}\n'.format(i['ts'], i['summary']))
        emailMessage += ('\n')

    for r in options.recipients:
        mimeMessage = MIMEText(emailMessage)
        mimeMessage['To'] = email.utils.formataddr((r, r))
        mimeMessage['From'] = email.utils.formataddr(('MozDef', options.sender))
        mimeMessage['Date'] = toUTC(datetime.now()).isoformat()
        mimeMessage['Subject'] = 'MozDef Alert: Releng Signing Servers Successful SSH Access'

        smtpserver = smtplib.SMTP(host=options.smtpserver, port=25)
        smtpserver.sendmail(options.sender, [r], mimeMessage.as_string())
        smtpserver.quit()

def main():
    logger.debug('starting')
    logger.debug(options)
    es = pyes.ES((list('{0}'.format(s) for s in options.esservers)))
    # see if we have matches.
    summaryCounts = esSearch(es)
    if len(summaryCounts) > 0:
        sendResults(summaryCounts)
    logger.debug('finished')


def initConfig():
    # change this to your default zone for when it's not specified
    options.defaultTimeZone = getConfig('defaulttimezone', 'US/Pacific', options.configfile)
    # logging settings
    options.output = getConfig('output', 'stdout', options.configfile)  # output our log to stdout or syslog
    options.sysloghostname = getConfig('sysloghostname', 'localhost', options.configfile)  # syslog hostname
    options.syslogport = getConfig('syslogport', 514, options.configfile)  # syslog port
    # elastic search server settings
    options.esservers = list(getConfig('esservers', 'http://localhost:9200', options.configfile).split(','))
    # email settings
    options.smtpserver = getConfig('smtpserver', 'localhost', options.configfile)
    options.sender = getConfig('sender', 'donotreply@localhost.com', options.configfile)
    options.recipients = list(getConfig('recipients', 'noone@localhost.com', options.configfile).split(','))

if __name__ == '__main__':
    parser = OptionParser()
    parser.add_option("-c", dest='configfile', default=sys.argv[0].replace('.py', '.conf'), help="configuration file to use")
    (options, args) = parser.parse_args()
    initConfig()
    initLogger()
    main()
