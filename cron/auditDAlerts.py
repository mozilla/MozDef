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

import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), "../lib"))
from utilities.toUTC import toUTC
from elasticsearch_client import ElasticsearchClient, ElasticsearchBadServer
from query_models import SearchQuery, TermMatch, ExistsMatch, QueryStringMatch, PhraseMatch


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


def esShadowSearch():
    # find stuff like cat /etc/shadow
    #  search for events within the date range that haven't already been alerted (i.e. given an alerttimestamp)
    search_query = SearchQuery(minutes=30)

    search_query.add_must([
        TermMatch('_type', 'auditd'),
        ExistsMatch('suser')
    ])

    search_query.add_should(PhraseMatch('command', 'shadow'))

    search_query.add_must_not([
        ExistsMatch('alerttimestamp'),
        PhraseMatch("cwd", "/var/backups"),
        PhraseMatch("dproc", "/usr/bin/glimpse"),
        PhraseMatch("dproc", "/bin/chmod"),
        PhraseMatch('command', 'cmp -s shadow.bak /etc/shadow'),
        PhraseMatch('command', 'cp -p /etc/shadow shadow.bak'),
        PhraseMatch('suser', 'infrasec'),
        PhraseMatch('parentprocess', 'mig-agent'),
        PhraseMatch('parentprocess', 'passwd'),
        PhraseMatch('command', 'no drop shadow'),
        PhraseMatch('command', 'js::shadow'),
        PhraseMatch('command', 'target.new'),
        PhraseMatch('command', '/usr/share/man'),
        PhraseMatch('command', 'shadow-invert.png'),
        PhraseMatch('command', 'ruby-shadow'),
        QueryStringMatch('command:gzip'),
        QueryStringMatch('command:http'),
        QueryStringMatch('command:html')
    ])

    return search_query


def esRPMSearch():
    search_query = SearchQuery(minutes=30)

    search_query.add_must([
        TermMatch('_type', 'auditd'),
        TermMatch('dproc', 'rpm'),
        ExistsMatch('suser')
    ])

    search_query.add_should([
        PhraseMatch("command", "-e"),
        PhraseMatch("command", "--erase"),
        PhraseMatch("command", "-i"),
        PhraseMatch("command", "--install"),
    ])

    search_query.add_must_not([
        ExistsMatch('alerttimestamp'),
        PhraseMatch("command", "--eval"),
        PhraseMatch("command", "--info"),
        PhraseMatch("dhost", "deploy"),          # ignore rpm builds on deploy hosts
        PhraseMatch("parentprocess", "puppet"),  # ignore rpm -e hp
    ])

    return search_query


def esYumSearch():
    search_query = SearchQuery(minutes=30)

    search_query.add_must([
        TermMatch('_type', 'auditd'),
        TermMatch('fname', 'yum'),
        ExistsMatch('suser')
    ])

    search_query.add_should(PhraseMatch('command', 'remove'))

    search_query.add_must_not([
        ExistsMatch('alerttimestamp'),
        PhraseMatch('fname', 'yum.conf')
    ])

    return search_query


def esGCCSearch():
    search_query = SearchQuery(minutes=30)

    search_query.add_must([
        TermMatch('_type', 'auditd'),
        TermMatch('fname', 'gcc'),
        ExistsMatch('command'),
        ExistsMatch('suser'),

    ])

    search_query.add_must_not([
        ExistsMatch('alerttimestamp'),
        QueryStringMatch("command:conftest.c dhave_config_h"),
        PhraseMatch("command", "gcc -v"),
        PhraseMatch("command", "gcc -e"),
        PhraseMatch("command", "gcc --version"),
        PhraseMatch("command", "gcc -qversion"),
        PhraseMatch("command", "gcc --help"),
        PhraseMatch("parentprocess", "gcc"),
        QueryStringMatch("parentprocess:g++ c++ make imake configure python python2 python2.6 python2.7"),
        PhraseMatch("suser", "root"),
        PhraseMatch("dhost", "jenkins1"),
        PhraseMatch("command", "gcc -Wl,-t -o /tmp"),
    ])

    return search_query


def esHistoryModSearch():
    search_query = SearchQuery(minutes=30)

    search_query.add_must([
        TermMatch('_type', 'auditd'),
        ExistsMatch('command'),
        ExistsMatch('suser'),
        QueryStringMatch("parentprocess:bash sh ksh"),
        QueryStringMatch("command:bash_history sh_history zsh_history .history secure messages history")
    ])

    search_query.add_should([
        QueryStringMatch("command:rm vi vim nano emacs"),
        PhraseMatch("command", "history -c")
    ])

    search_query.add_must_not(ExistsMatch('alerttimestamp'))

    return search_query


def esRunSearch(es, query, aggregateField, detailLimit=5):
    try:
        full_results = query.execute(es)

        # correlate any matches by the aggregate field.
        # make a simple list of indicator values that can be counted/summarized by Counter
        resultsIndicators = list()

        results = full_results['hits']
        for r in results:
            resultsIndicators.append(r['_source']['details'][aggregateField])

        # use the list of tuples ('indicator',count) to create a dictionary with:
        # indicator,count,es records
        # and add it to a list to return.
        indicatorList = list()
        for i in Counter(resultsIndicators).most_common():
            idict = dict(indicator=i[0], count=i[1], events=[])
            for r in results:
                if r['_source']['details'][aggregateField].encode('ascii', 'ignore') == i[0]:
                    # copy events detail into this correlation up to our detail limit
                    if len(idict['events']) < detailLimit:
                        idict['events'].append(r)
            indicatorList.append(idict)
        return indicatorList

    except ElasticsearchBadServer:
        logger.error('Elastic Search server could not be reached, check network connectivity')


def createAlerts(es, indicatorCounts):
    '''given a list of dictionaries:
        count: X
        indicator: sometext
        events: list of ES results matching the indicator

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
                    alert['summary'] = ('suspicious command: {0}'.format(i['indicator']))
                else:
                    alert['summary'] = ('{0} suspicious commands: {1}'.format(i['count'], i['indicator']))
                for e in i['events'][:3]:
                    if 'dhost' in e['_source']['details'].keys():
                        alert['summary'] += ' on {0}'.format(e['_source']['details']['dhost'])
                    # first 50 chars of a command, then ellipsis
                    alert['summary'] += ' {0}'.format(e['_source']['details']['command'][:50] + (e['_source']['details']['command'][:50] and '...'))

                for e in i['events']:
                    # append the relevant events in text format to avoid errant ES issues.
                    # should be able to just set eventsource to i['events'] but different versions of ES 1.0 complain
                    alert['eventsource'].append(flattenDict(e))

                logger.debug(alert['summary'])
                logger.debug(alert['events'])
                logger.debug(alert)

                # save alert to alerts index, update events index with alert ID for cross reference
                alertResult = alertToES(es, alert)

                ##logger.debug(alertResult)
                # for each event in this list of indicatorCounts
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
    es = ElasticsearchClient((list('{0}'.format(s) for s in options.esservers)))
    # run a series of searches for suspicious commands
    # aggregating by a specific field (usually dhost or suser)
    # and alert if found

    # /etc/shadow manipulation by destination host
    indicatorCounts = esRunSearch(es, esShadowSearch(), 'suser')
    createAlerts(es, indicatorCounts)

    # search for rpm -i or -e type commands by suser:
    indicatorCounts = esRunSearch(es, esRPMSearch(), 'suser')
    createAlerts(es, indicatorCounts)

    # search for yum remove commands by suser:
    indicatorCounts = esRunSearch(es, esYumSearch(), 'suser')
    createAlerts(es, indicatorCounts)

    # search for gcc commands by suser:
    indicatorCounts = esRunSearch(es, esGCCSearch(), 'suser')
    createAlerts(es, indicatorCounts)

    # search for history modification commands by suser:
    indicatorCounts = esRunSearch(es, esHistoryModSearch(), 'suser')
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
