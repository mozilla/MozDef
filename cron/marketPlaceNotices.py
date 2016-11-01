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
from collections import Counter
from configlib import getConfig, OptionParser
from datetime import datetime
from email.mime.text import MIMEText
from logging.handlers import SysLogHandler

import sys
import os
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../lib'))
from utilities.toUTC import toUTC
from elasticsearch_client import ElasticsearchClient, ElasticsearchBadServer
from query_models import SearchQuery, TermMatch, PhraseMatch, RangeMatch


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


def esSearch(es):
    search_query = SearchQuery(minutes=60)
    search_query.add_must([
        TermMatch('deviceproduct', 'webpay'),
        PhraseMatch('details.dhost', 'marketplace.firefox.com'),
        RangeMatch('details.severity', from_value=6)
    ])
    search_query.add_must_not(PhraseMatch('details.dhost', 'marketplace-dev.allizom.org'))

    try:
        full_results = search_query.execute(es)
        # correlate any matches
        # make a simple list of indicator values that can be counted/summarized by Counter
        resultsIndicators = list()
        results = full_results['hits']
        for r in results:
            resultsIndicators.append(r['_source']['details']['request'])

        # use the list of tuples ('indicator',count) to create a dictionary with:
        # indicator,count,es records
        # and add it to a list to return.
        indicatorList = list()
        for i in Counter(resultsIndicators).most_common():
            idict = dict(indicator=i[0], count=i[1], events=[])
            for r in results:
                if r['_source']['details']['request'].encode('ascii', 'ignore') == i[0]:
                    idict['events'].append(r)
            indicatorList.append(idict)
        return indicatorList

    except ElasticsearchBadServer:
        logger.error('Elastic Search server could not be reached, check network connectivity')

def sendResults(indicatorCounts):
    emailMessage = ''

    for i in indicatorCounts:
        emailMessage += ('Count: {0} Endpoint: {1:>20}\n'.format(i['count'], i['indicator']))

        for event in i['events']:
            emailMessage += ('{0:>10}:\n'.format('event'))
            for k, v in event['_source'].iteritems():

                #sys.stdout.write('\t\t{0}\n\n'.format(json.dumps(event['_source'], indent=4, sort_keys=True)))
                if k == 'details':
                    emailMessage += ('{0:>20}:'.format('details'))
                    emailMessage += ('{0:>30}'.format(
                        json.dumps(v,
                                   indent=16,
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
        mimeMessage['Subject'] = 'Marketplace Alert Summary'

        smtpserver = smtplib.SMTP(host=options.smtpserver, port=25)
        smtpserver.sendmail(options.sender, [r], mimeMessage.as_string())
        smtpserver.quit()

def main():
    logger.debug('starting')
    logger.debug(options)
    es = ElasticsearchClient((list('{0}'.format(s) for s in options.esservers)))
    # see if we have matches.
    indicatorCounts = esSearch(es)
    if len(indicatorCounts) > 0:
        sendResults(indicatorCounts)
    logger.debug('finished')


def initConfig():
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
