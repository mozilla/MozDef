#!/usr/bin/env python
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Contributors:
# Jeff Bryner jbryner@mozilla.com

import sys
import json
import logging
import pika
from collections import Counter
from configlib import getConfig, OptionParser
from datetime import datetime
from logging.handlers import SysLogHandler

import sys
import os
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../lib'))
from utilities.toUTC import toUTC
from elasticsearch_client import ElasticsearchClient, ElasticsearchBadServer
from query_models import SearchQuery, TermMatch, PhraseMatch, ExistsMatch


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


def flattenDict(dictIn):
    sout = ''
    for k, v in dictIn.iteritems():
        sout += '{0}: {1} '.format(k, v)
    return sout


def alertToMessageQueue(alertDict):
    try:
        connection = pika.BlockingConnection(pika.ConnectionParameters(host=options.mqserver))
        channel = connection.channel()
        # declare the exchanges
        channel.exchange_declare(exchange=options.alertexchange, type='topic', durable=True)

        # cherry pick items from the alertDict to send to the alerts messageQueue
        mqAlert = dict(severity='INFO', category='')
        if 'severity' in alertDict.keys():
            mqAlert['severity'] = alertDict['severity']
        if 'category' in alertDict.keys():
            mqAlert['category'] = alertDict['category']
        if 'utctimestamp' in alertDict.keys():
            mqAlert['utctimestamp'] = alertDict['utctimestamp']
        if 'eventtimestamp' in alertDict.keys():
            mqAlert['eventtimestamp'] = alertDict['eventtimestamp']
        mqAlert['summary'] = alertDict['summary']
        logger.debug(mqAlert)
        channel.basic_publish(exchange=options.alertexchange, routing_key=options.alertqueue, body=json.dumps(mqAlert))
    except Exception as e:
        logger.error('Exception while sending alert to message queue: {0}'.format(e))


def alertToES(es, alertDict):
    try:
        res = es.save_alert(body=alertDict)
        return(res)
    except ElasticsearchBadServer:
        logger.error('Elastic Search server could not be reached, check network connectivity')


def esUserWriteSearch():
    search_query = SearchQuery(minutes=30)
    search_query.add_must([
        TermMatch('_type', 'auditd'),
        TermMatch('signatureid', 'write'),
        PhraseMatch('auditkey', 'user'),
        ExistsMatch('suser')
    ])
    search_query.add_must_not([
        ExistsMatch('alerttimestamp'),
        PhraseMatch('parentprocess', 'puppet dhclient-script')

    ])

    return search_query


def esRunSearch(es, query, aggregateField):
    try:
        full_results = query.execute(es)

        # correlate any matches by the aggregate field.
        # make a simple list of indicator values that can be counted/summarized by Counter
        resultsIndicators = list()

        results = full_results['hits']
        for r in results:
            if aggregateField in r['_source']['details']:
                resultsIndicators.append(r['_source']['details'][aggregateField])
            else:
                logger.error('{0} aggregate key not found {1}'.format(aggregateField, r['_source']))
                sys.exit(1)

        # use the list of tuples ('indicator',count) to create a dictionary with:
        # indicator,count,es records
        # and add it to a list to return.
        indicatorList = list()
        for i in Counter(resultsIndicators).most_common():
            idict = dict(indicator=i[0], count=i[1], events=[])
            for r in results:
                if r['_source']['details'][aggregateField].encode('ascii', 'ignore') == i[0]:
                    idict['events'].append(r)
            indicatorList.append(idict)
        return indicatorList

    except ElasticsearchBadServer:
        logger.error('Elastic Search server could not be reached, check network connectivity')


def createAlerts(es, indicatorCounts):
    '''given a list of dictionaries:
        count: X
        indicator: sometext
        events: list of pyes results matching the indicator

        1) create a summary alert with detail of the events
        2) update the events with an alert timestamp so they are not included in further alerts
    '''
    try:
        if len(indicatorCounts) > 0:
            for i in indicatorCounts:
                alert = dict(utctimestamp=toUTC(datetime.now()).isoformat(), severity='NOTICE', summary='', category='auditd', tags=['auditd'], eventsource=[], events=[])
                for e in i['events']:
                    alert['events'].append(
                        dict(documentindex=e['_index'],
                             documenttype=e['_type'],
                             documentsource=e['_source'],
                             documentid=e['_id']))
                alert['severity'] = 'NOTICE'
                if i['count']==1:
                    alert['summary'] = ('suspicious file access: {0} '.format(i['indicator']))
                else:
                    alert['summary'] = ('{0} suspicious file access: {1}'.format(i['count'], i['indicator']))
                for e in i['events'][:3]:
                    alert['summary'] += ' {0}'.format(e['_source']['details']['fname'])
                    if 'dhost' in e['_source']['details'].keys():
                        alert['summary'] += ' on {0}'.format(e['_source']['details']['dhost'])
                for e in i['events']:
                    # append the relevant events in text format to avoid errant ES issues.
                    # should be able to just set eventsource to i['events'] but different versions of ES 1.0 complain
                    alert['eventsource'].append(flattenDict(e))

                logger.debug(alert['summary'])
                logger.debug(alert['events'])
                logger.debug(alert)

                # save alert to alerts index, update events index with alert ID for cross reference
                alertResult = alertToES(es, alert)

                # logger.debug(alertResult)
                # for each event in this list of indicatorCounts
                # update with the alertid/index
                # and update the alerttimestamp on the event itself so it's not re-alerted
                for e in i['events']:
                    if 'alerts' not in e['_source'].keys():
                        e['_source']['alerts'] = []
                    e['_source']['alerts'].append(dict(index=alertResult['_index'], type=alertResult['_type'], id=alertResult['_id']))
                    e['_source']['alerttimestamp'] = toUTC(datetime.now()).isoformat()

                    es.save_object(index=e['_index'], doc_type=e['_type'], doc_id=e['_id'], body=e['_source'])

                alertToMessageQueue(alert)
    except ValueError as e:
        logger.error("Exception %r when creating alerts " % e)


def main():
    logger.debug('starting')
    logger.debug(options)
    es = ElasticsearchClient((list('{0}'.format(s) for s in options.esservers)))
    # searches for suspicious file access
    # aggregating by a specific field (usually dhost or suser)
    # and alert if found

    # signature: WRITE by a user, not by puppet
    indicatorCounts = esRunSearch(es, esUserWriteSearch(), 'suser')
    createAlerts(es, indicatorCounts)

    logger.debug('finished')


def initConfig():
    # msg queue settings
    options.mqserver = getConfig('mqserver', 'localhost', options.configfile)  # message queue server hostname
    options.alertqueue = getConfig('alertqueue', 'mozdef.alert', options.configfile)  # alert queue topic
    options.alertexchange = getConfig('alertexchange', 'alerts', options.configfile)  # alert queue exchange name
    # logging settings
    options.output = getConfig('output', 'stdout', options.configfile)  # output our log to stdout or syslog
    options.sysloghostname = getConfig('sysloghostname', 'localhost', options.configfile)  # syslog hostname
    options.syslogport = getConfig('syslogport', 514, options.configfile)  # syslog port
    # elastic search server settings
    options.esservers = list(getConfig('esservers', 'http://localhost:9200', options.configfile).split(','))

if __name__ == '__main__':
    parser = OptionParser()
    parser.add_option("-c", dest='configfile', default=sys.argv[0].replace('.py', '.conf'), help="configuration file to use")
    (options, args) = parser.parse_args()
    initConfig()
    initLogger()
    main()
