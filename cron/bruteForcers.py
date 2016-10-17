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
import netaddr
import pika
import pytz
import pyes
from collections import Counter
from configlib import getConfig, OptionParser
from datetime import datetime
from datetime import timedelta
from dateutil.parser import parse
from logging.handlers import SysLogHandler

import sys
import os
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../lib'))
from utilities.toUTC import toUTC

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
        channel.basic_publish(exchange=options.alertexchange, routing_key=options.alertqueue, body=json.dumps(mqAlert))
    except Exception as e:
        logger.error('Exception while sending alert to message queue: {0}'.format(e))


def alertToES(es, alertDict):
    try:
        res = es.index(index='alerts', doc_type='alert', doc=alertDict)
        return(res)
    except pyes.exceptions.NoServerAvailable:
        logger.error('Elastic Search server could not be reached, check network connectivity')


def esSearch(es, begindateUTC=None, enddateUTC=None):
    resultsList = list()
    if begindateUTC is None:
        begindateUTC = toUTC(datetime.now() - timedelta(minutes=15))
    if enddateUTC is None:
        enddateUTC = toUTC(datetime.now())
    try:
        # search for events within the date range that haven't already been alerted (i.e. given an alerttimestamp)
        qDate = pyes.RangeQuery(qrange=pyes.ESRange('utctimestamp', from_value=begindateUTC, to_value=enddateUTC))
        q = pyes.ConstantScoreQuery(pyes.MatchAllQuery())
        qType = pyes.TermFilter('_type', 'event')
        qSystems = pyes.TermFilter('eventsource','systemslogs')
        qFail = pyes.QueryFilter(pyes.MatchQuery('summary','failed','phrase'))
        qssh = pyes.TermFilter('program','sshd')
        q = pyes.FilteredQuery(q,pyes.BoolFilter(
            must=[qType,qSystems,qFail,qssh,qDate],
            should=[
                pyes.QueryFilter(pyes.MatchQuery('summary',
                                                 'login ldap_count_entries',
                                                 'boolean'))],
            must_not=[
                pyes.ExistsFilter('alerttimestamp'),
                pyes.QueryFilter(pyes.MatchQuery('summary','10.22.8.128','phrase')),
                pyes.QueryFilter(pyes.MatchQuery('summary','10.8.75.35','phrase')),
                pyes.QueryFilter(pyes.MatchQuery('summary','208.118.237.','phrase'))
        ]))
        results=es.search(q,indices='events')
        # grab the results before iterating them to avoid pyes bug
        rawresults=results._search_raw()
        alerts=list()
        ips=list()

        # see if any of these failed attempts cross our threshold per source ip
        for r in rawresults['hits']['hits'][:]:
            if 'details' in r['_source'].keys() and 'sourceipaddress' in r['_source']['details']:
                ips.append(r['_source']['details']['sourceipaddress'])
            else:
                #search for an ip'ish thing in the summary
                for w in r['_source']['summary'].strip().split():
                    if netaddr.valid_ipv4(w.strip("'")) or netaddr.valid_ipv6(w.strip("'")):
                        ips.append(w.strip("'"))

        for i in Counter(ips).most_common():
            if i[1]>= options.threshold:
                # create an alert dictionary
                alertDict=dict(sourceiphits=i[1],
                               sourceipaddress=str(netaddr.IPAddress(i[0])),
                               events=[])
                # add source events
                for r in rawresults['hits']['hits']:
                    if 'details' in r['_source'].keys() and 'sourceipaddress' in r['_source']['details'] and r['_source']['details']['sourceipaddress'].encode('ascii', 'ignore') == i[0]:
                        alertDict['events'].append(r)
                alerts.append(alertDict)
        return alerts

    except pyes.exceptions.NoServerAvailable:
        logger.error('Elastic Search server could not be reached, check network connectivity')


def createAlerts(es, alerts):
    '''given a list of dictionaries:
        sourceiphits (int)
        sourceipv4address (ip a string)
        events: a list of pyes results maching the alert
        1) create a summary alert with detail of the events
        2) update the events with the alert timestamp and ID

    '''
    try:
        if len(alerts) > 0:
            for i in alerts:
                alert = dict(utctimestamp=toUTC(datetime.now()).isoformat(), severity='NOTICE', summary='', category='bruteforce', tags=['ssh'], eventsource=[], events=[])
                for e in i['events']:
                    alert['events'].append(
                        dict(documentindex=e['_index'],
                             documenttype=e['_type'],
                             documentsource=e['_source'],
                             documentid=e['_id']))
                alert['severity'] = 'NOTICE'
                alert['summary'] = ('{0} ssh bruteforce attempts by {1}'.format(i['sourceiphits'], i['sourceipaddress']))
                for e in i['events'][:3]:
                    if 'details' in e.keys() and 'hostname' in e['details']:
                        alert['summary'] += ' on {0}'.format(e['_source']['details']['hostname'])

                logger.debug(alert)

                # save alert to alerts index, update events index with alert ID for cross reference
                alertResult = alertToES(es, alert)

                # for each event in this list
                # update with the alertid/index
                # and update the alerttimestamp on the event itself so it's not re-alerted
                for e in i['events']:
                    if 'alerts' not in e['_source'].keys():
                        e['_source']['alerts'] = []
                    e['_source']['alerts'].append(dict(index=alertResult['_index'], type=alertResult['_type'], id=alertResult['_id']))
                    e['_source']['alerttimestamp'] = toUTC(datetime.now()).isoformat()

                    es.update(e['_index'], e['_type'], e['_id'], document=e['_source'])

                alertToMessageQueue(alert)
    except ValueError as e:
        logger.error("Exception %r when creating alerts " % e)


def main():
    logger.debug('starting')
    logger.debug(options)
    es = pyes.ES((list('{0}'.format(s) for s in options.esservers)))
    # see if we have matches.
    alerts = esSearch(es)
    createAlerts(es, alerts)
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
    # threshold settings
    options.threshold = getConfig('threshold', 2, options.configfile)

if __name__ == '__main__':
    parser = OptionParser()
    parser.add_option("-c", dest='configfile', default=sys.argv[0].replace('.py', '.conf'), help="configuration file to use")
    (options, args) = parser.parse_args()
    initConfig()
    initLogger()
    main()
