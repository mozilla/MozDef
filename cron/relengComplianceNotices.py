#!/usr/bin/env python
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Contributors:
# Jeff Bryner jbryner@mozilla.com

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
        begindateUTC = toUTC(datetime.now() - timedelta(hours=24))
    if enddateUTC is None:
        enddateUTC = toUTC(datetime.now())
    try:
        # search for events within the date range
        qDate = pyes.RangeQuery(qrange=pyes.ESRange('utctimestamp',
                                                    from_value=begindateUTC,
                                                    to_value=enddateUTC))

        q = pyes.ConstantScoreQuery(pyes.MatchAllQuery())

        q = pyes.FilteredQuery(q,pyes.BoolFilter(must=[qDate,
                                                       pyes.TermFilter('check.ref', 'sysmediumpackages1'),
                                                       pyes.TermFilter('tags.operator','releng'),
                                                       pyes.QueryFilter(pyes.MatchQuery('check.ref', 'sysmediumpackages1 syslowdns1', 'boolean')),
                                                       pyes.TermFilter('compliance', 'false')
                                                       ]))

        pyesresults = es.search(q, size=1000, indices='complianceitems')
        logger.debug(pyesresults.count())

        # correlate any matches
        # make a simple list of indicator values that can be counted/summarized by Counter
        resultsTargets = list()

        # bug in pyes..capture results as raw list or it mutates after first access:
        # copy the hits.hits list as our resusts, which is the same as the official elastic search library returns.
        results = pyesresults._search_raw()['hits']['hits']
        for r in results:
            # get the hostname
            resultsTargets.append(r['_source']['target'])

        # use the list of tuples ('hostname',count) to create a dictionary with:
        # indicator,count,es records
        # and add it to a list to return.
        indicatorList = list()
        for i in Counter(resultsTargets).most_common():
            idict = dict(indicator=i[0], count=i[1], events=[])
            for r in results:
                if r['_source']['target'].encode('ascii', 'ignore') == i[0]:
                    idict['events'].append(r)
            indicatorList.append(idict)
        return indicatorList

    except pyes.exceptions.NoServerAvailable:
        logger.error('Elastic Search server could not be reached, check network connectivity')

def sendResults(indicatorCounts):
    emailMessage = ''

    for i in indicatorCounts:
        emailMessage += ('Count: {0} Endpoint: {1:>20}\n'.format(i['count'], i['indicator']))

        for event in i['events']:
            emailMessage += ('{0:>10}:\n'.format('Detail'))
            for k, v in event['_source'].iteritems():

                #sys.stdout.write('\t\t{0}\n\n'.format(json.dumps(event['_source'], indent=4, sort_keys=True)))
                if k in ['policy', 'tags', 'check']:
                    emailMessage += ('{0:>20}:'.format(k))
                    emailMessage += ('{0:>30}'.format(
                        json.dumps(v,
                                   indent=20,
                                   sort_keys=True)
                        .replace('{', '')
                        .replace('}', '')))
                elif k not in ('utctimestamp', 'receivedtimestamp'):
                    emailMessage += ('{0:>20}: {1}\n'.format(k, v))
        emailMessage += ('\n')

    for r in options.recipients:
        mimeMessage = MIMEText(emailMessage)
        mimeMessage['To'] = email.utils.formataddr((r, r))
        mimeMessage['From'] = email.utils.formataddr(('MozDef', options.sender))
        mimeMessage['Date'] = toUTC(datetime.now()).isoformat()
        mimeMessage['Subject'] = 'Releng Compliance Summary--out of compliance'

        smtpserver = smtplib.SMTP(host=options.smtpserver, port=25)
        smtpserver.sendmail(options.sender, [r], mimeMessage.as_string())
        smtpserver.quit()

def main():
    logger.debug('starting')
    logger.debug(options)
    es = pyes.ES((list('{0}'.format(s) for s in options.esservers)))
    # see if we have matches.
    indicatorCounts = esSearch(es)
    if len(indicatorCounts) > 0:
        sendResults(indicatorCounts)
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
