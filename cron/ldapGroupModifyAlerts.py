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
    if type(suspectedDate) == str:
        objDate = parse(suspectedDate, fuzzy=True)
    elif type(suspectedDate) == datetime:
        objDate = suspectedDate

    if objDate.tzinfo is None:
        objDate = pytz.timezone(localTimeZone).localize(objDate)
        objDate = utc.normalize(objDate)
    else:
        objDate = utc.normalize(objDate)
    if objDate is not None:
        objDate = utc.normalize(objDate)

    return objDate


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
        mqAlert['summary'] = alertDict['summary'].replace(',dc=mozilla', '')
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
        qType = pyes.TermFilter('category', 'ldapChange')
        qAlerted = pyes.ExistsFilter('alerttimestamp')
        qModify = pyes.QueryFilter(pyes.MatchQuery("changetype","modify","phrase"))
        qGroup = pyes.QueryFilter(pyes.MatchQuery("dn","groups"))        

        q = pyes.ConstantScoreQuery(pyes.MatchAllQuery())
        q = pyes.FilteredQuery(q,pyes.BoolFilter(must=[qDate, qType, qModify, qGroup],must_not=[qAlerted]))
        results=es.search(q,size=1000,indices='events,events-previous')
        # grab the results before iterating them to avoid pyes bug
        rawresults=results._search_raw()
        alerts=list()
        for r in rawresults['hits']['hits']:
            alert = dict(
                utctimestamp=toUTC(datetime.now()).isoformat(),
                severity='INFO',
                summary='{0}'.format(r['_source']['summary']),
                category='ldap',
                tags=['ldap'],
                eventsource=[],
                events=[])
            alert['events'].append(
                dict(documentid=r['_id'],
                     documenttype=r['_type'],
                     documentindex=r['_index'],
                     documentsource=r['_source']))
            alerts.append(alert)
        return alerts

    except pyes.exceptions.NoServerAvailable:
        logger.error('Elastic Search server could not be reached, check network connectivity')


def createAlerts(es, alerts):
    '''given a list of dictionaries:
        1) save the alert to ES
        2) update the events with an alert timestamp so they are not included in further alerts
    '''
    try:
        if len(alerts) > 0:
            for alert in alerts:
                # save alert to alerts index, update events index with alert ID for cross reference
                alertResult = alertToES(es, alert)

                ##logger.debug(alertResult)
                # for each event in this list of indicatorCounts
                # update with the alertid/index
                # and update the alerttimestamp on the event itself so it's not re-alerted
                for e in alert['events']:
                    if 'alerts' not in e['documentsource'].keys():
                        e['documentsource']['alerts'] = []
                    e['documentsource']['alerts'].append(
                        dict(index=alertResult['_index'],
                             type=alertResult['_type'],
                             id=alertResult['_id']))
                    e['documentsource']['alerttimestamp'] = toUTC(datetime.now()).isoformat()
                    es.update(e['documentindex'], e['documenttype'], e['documentid'], document=e['documentsource'])

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
    # change this to your default zone for when it's not specified
    options.defaultTimeZone = getConfig('defaulttimezone', 'US/Pacific', options.configfile)
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
