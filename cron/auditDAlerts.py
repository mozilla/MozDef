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


def toUTC(suspectedDate, localTimeZone="UTC"):
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
        mqAlert['summary'] = alertDict['summary']
        logger.debug(mqAlert)
        channel.basic_publish(exchange=options.alertexchange, routing_key=options.alertqueue, body=json.dumps(mqAlert))
    except Exception as e:
        logger.error('Exception while sending alert to message queue: {0}'.format(e))


def alertToES(es, alertDict):
    try:
        res = es.index(index='alerts', doc_type='alert', doc=alertDict)
        return(res)
    except pyes.exceptions.NoServerAvailable:
        logger.error('Elastic Search server could not be reached, check network connectivity')

def esShadowSearch():
    # find stuff like cat /etc/shadow
    #  search for events within the date range that haven't already been alerted (i.e. given an alerttimestamp)
    begindateUTC = toUTC(datetime.now() - timedelta(minutes=30))
    enddateUTC = toUTC(datetime.now())
    qDate = pyes.RangeQuery(qrange=pyes.ESRange('utctimestamp', from_value=begindateUTC, to_value=enddateUTC))
    qType = pyes.TermFilter('_type', 'auditd')
    qEvents = pyes.TermFilter('command', 'shadow')
    qalerted = pyes.ExistsFilter('alerttimestamp')
    q=pyes.ConstantScoreQuery(pyes.MatchAllQuery())
    # query must match dates, should have keywords must not match whitelisted items
    q.filters.append(
        pyes.BoolFilter(
            must=[qType,
                  qDate,
                  pyes.ExistsFilter('suser')],
            should=[qEvents],
            must_not=[
                qalerted,
                pyes.QueryFilter(pyes.MatchQuery("cwd","/var/backups","phrase")),
                pyes.QueryFilter(pyes.MatchQuery("dproc","/usr/bin/glimpse","phrase")),
                pyes.QueryFilter(pyes.MatchQuery("dproc","/bin/chmod","phrase")),
                pyes.QueryFilter(pyes.MatchQuery('command', 'cmp -s shadow.bak /etc/shadow',"phrase")),
                pyes.QueryFilter(pyes.MatchQuery('command', 'cp -p /etc/shadow shadow.bak',"phrase")),
                pyes.QueryFilter(pyes.MatchQuery('suser', 'infrasec',"phrase")),
                pyes.QueryFilter(pyes.MatchQuery('parentprocess', 'mig-agent',"phrase")),
                pyes.QueryFilter(pyes.MatchQuery('parentprocess', 'passwd',"phrase")),
                pyes.QueryFilter(pyes.MatchQuery('command', 'no drop shadow',"phrase")),
                pyes.QueryFilter(pyes.MatchQuery('command', 'js::shadow',"phrase")),
                pyes.QueryFilter(pyes.MatchQuery('command', 'target.new',"phrase")),
                pyes.QueryFilter(pyes.MatchQuery('command', '/usr/share/man',"phrase")),
                pyes.QueryFilter(pyes.MatchQuery('command', 'shadow-invert.png',"phrase")),
                pyes.QueryFilter(pyes.MatchQuery('command', 'ruby-shadow',"phrase")),
                pyes.QueryFilter(pyes.QueryStringQuery('command:gzip')),
                pyes.QueryFilter(pyes.QueryStringQuery('command:http')),
                pyes.QueryFilter(pyes.QueryStringQuery('command:html'))
    ]))
    return q


def esRPMSearch():
    begindateUTC= toUTC(datetime.now() - timedelta(minutes=30))
    enddateUTC= toUTC(datetime.now())
    qDate = pyes.RangeQuery(qrange=pyes.ESRange('utctimestamp', from_value=begindateUTC, to_value=enddateUTC))
    qType = pyes.TermFilter('_type', 'auditd')
    qEvents = pyes.TermFilter("dproc","rpm")
    qalerted = pyes.ExistsFilter('alerttimestamp')
    q=pyes.ConstantScoreQuery(pyes.MatchAllQuery())
    q.filters.append(pyes.BoolFilter(must=[qType, qDate,qEvents,
                                           pyes.ExistsFilter('suser')], 
        should=[
        pyes.QueryFilter(pyes.MatchQuery("command","-e","phrase")),
        pyes.QueryFilter(pyes.MatchQuery("command","--erase","phrase")),
        pyes.QueryFilter(pyes.MatchQuery("command","-i","phrase")),
        pyes.QueryFilter(pyes.MatchQuery("command","--install","phrase"))
        ],
        must_not=[
        qalerted,
        pyes.QueryFilter(pyes.MatchQuery("command","--eval","phrase")),
        pyes.QueryFilter(pyes.MatchQuery("command","--info","phrase")),
        pyes.QueryFilter(pyes.MatchQuery("dhost","deploy","phrase")),         # ignore rpm builds on deploy hosts
        pyes.QueryFilter(pyes.MatchQuery("parentprocess","puppet","phrase")), # ignore rpm -e hp 
        ]))    
    return q

def esYumSearch():
    begindateUTC= toUTC(datetime.now() - timedelta(minutes=30))
    enddateUTC= toUTC(datetime.now())
    qDate = pyes.RangeQuery(qrange=pyes.ESRange('utctimestamp', from_value=begindateUTC, to_value=enddateUTC))
    qType = pyes.TermFilter('_type', 'auditd')
    qEvents = pyes.TermFilter("fname","yum")
    qalerted = pyes.ExistsFilter('alerttimestamp')
    q=pyes.ConstantScoreQuery(pyes.MatchAllQuery())
    q.filters.append(pyes.BoolFilter(must=[qType, qDate,qEvents,
                                           pyes.ExistsFilter('suser')], 
        should=[
        pyes.QueryFilter(pyes.MatchQuery("command","remove","phrase"))
        ],
        must_not=[
        qalerted,
        pyes.QueryFilter(pyes.MatchQuery("fname","yum.conf","phrase"))
        ]))
    return q

def esGCCSearch():
    begindateUTC= toUTC(datetime.now() - timedelta(minutes=30))
    enddateUTC= toUTC(datetime.now())
    qDate = pyes.RangeQuery(qrange=pyes.ESRange('utctimestamp', from_value=begindateUTC, to_value=enddateUTC))
    qType = pyes.TermFilter('_type', 'auditd')
    qEvents = pyes.TermFilter("fname","gcc")
    qCommand = pyes.ExistsFilter('command')
    qalerted = pyes.ExistsFilter('alerttimestamp')
    q=pyes.ConstantScoreQuery(pyes.MatchAllQuery())
    q.filters.append(
        pyes.BoolFilter(must=[qType,
                              qDate,
                              qEvents,
                              qCommand,
                              pyes.ExistsFilter('suser')                              
                            ],
    must_not=[
        qalerted,
        pyes.QueryFilter(pyes.MatchQuery("command","conftest.c dhave_config_h","boolean")),
        pyes.QueryFilter(pyes.MatchQuery("command","gcc -v","phrase")),
        pyes.QueryFilter(pyes.MatchQuery("command","gcc -e","phrase")),
        pyes.QueryFilter(pyes.MatchQuery("command","gcc --version","phrase")),
        pyes.QueryFilter(pyes.MatchQuery("command","gcc -qversion","phrase")),
        pyes.QueryFilter(pyes.MatchQuery("command","gcc --help","phrase")),
        pyes.QueryFilter(pyes.MatchQuery("parentprocess","gcc","phrase")),
        pyes.QueryFilter(pyes.MatchQuery("parentprocess","g++ c++ make imake configure python python2 python2.6 python2.7","boolean")),
        pyes.QueryFilter(pyes.MatchQuery("suser","root","phrase")),
        pyes.QueryFilter(pyes.MatchQuery("dhost","jenkins1","boolean")),
        pyes.QueryFilter(pyes.MatchQuery("command","gcc -Wl,-t -o /tmp","phrase"))
        ]))
    return q

def esHistoryModSearch():
    begindateUTC= toUTC(datetime.now() - timedelta(minutes=30))
    enddateUTC= toUTC(datetime.now())
    qDate = pyes.RangeQuery(qrange=pyes.ESRange('utctimestamp', from_value=begindateUTC, to_value=enddateUTC))
    qType = pyes.TermFilter('_type', 'auditd')
    qCommand = pyes.ExistsFilter('command')
    qalerted = pyes.ExistsFilter('alerttimestamp')
    q=pyes.ConstantScoreQuery(pyes.MatchAllQuery())
    q.filters.append(
        pyes.BoolFilter(must=[
                            qType, qDate,qCommand,
                            pyes.ExistsFilter('suser'), 
                            pyes.QueryFilter(pyes.MatchQuery("parentprocess","bash sh ksh","boolean")),
                            pyes.QueryFilter(pyes.MatchQuery("command","bash_history sh_history zsh_history .history secure messages history","boolean"))
                            ],
    should=[
        
        pyes.QueryFilter(pyes.MatchQuery("command","rm vi vim nano emacs","boolean")),
        pyes.QueryFilter(pyes.MatchQuery("command","history -c","phrase"))
        
    ],
    must_not=[
        qalerted
        ]))
    return q

def esRunSearch(es, query, aggregateField, detailLimit=5):
    try:
        pyesresults = es.search(query, size=1000, indices='events,events-previous')
        # logger.debug(results.count())

        # correlate any matches by the aggregate field.
        # make a simple list of indicator values that can be counted/summarized by Counter
        resultsIndicators = list()

        # bug in pyes..capture results as raw list or it mutates after first access:
        # copy the hits.hits list as our results, which is the same as the official elastic search library returns.
        results = pyesresults._search_raw()['hits']['hits']
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
                    if len(idict['events'])<detailLimit:
                        idict['events'].append(r)
            indicatorList.append(idict)
        return indicatorList

    except pyes.exceptions.NoServerAvailable:
        logger.error('Elastic Search server could not be reached, check network connectivity')        
    
def esSearch(es, begindateUTC=None, enddateUTC=None):
    if begindateUTC is None:
        begindateUTC = toUTC(datetime.now() - timedelta(minutes=80))
    if enddateUTC is None:
        enddateUTC = toUTC(datetime.now())
    try:
        # search for events within the date range that haven't already been alerted (i.e. given an alerttimestamp)
        qDate = pyes.RangeQuery(qrange=pyes.ESRange('utctimestamp', from_value=begindateUTC, to_value=enddateUTC))
        qType = pyes.TermFilter('_type', 'auditd')
        qEvents = pyes.TermFilter('command', 'shadow')
        qalerted = pyes.ExistsFilter('alerttimestamp')
        q=pyes.ConstantScoreQuery(pyes.MatchAllQuery())
        # query must match dates, should have keywords must not match whitelisted items
        q.filters.append(pyes.BoolFilter(must=[qType, qDate ], should=[qEvents],must_not=[
            qalerted,
            pyes.QueryFilter(pyes.MatchQuery("cwd","/var/backups","phrase")),
            pyes.QueryFilter(pyes.MatchQuery("dproc","/usr/bin/glimpse","phrase")),
            pyes.QueryFilter(pyes.MatchQuery("dproc","/bin/chmod","phrase")),
            pyes.QueryFilter(pyes.MatchQuery('command', 'cmp -s shadow.bak /etc/shadow',"phrase")),
            pyes.QueryFilter(pyes.MatchQuery('command', 'cp -p /etc/shadow shadow.bak',"phrase")),
            pyes.QueryFilter(pyes.MatchQuery('suser', 'infrasec',"phrase")),
            pyes.QueryFilter(pyes.MatchQuery('parentprocess', 'mig-agent',"phrase")),
            pyes.QueryFilter(pyes.MatchQuery('parentprocess', 'passwd',"phrase")),
            pyes.QueryFilter(pyes.MatchQuery('command', 'no drop shadow',"phrase")),
            pyes.QueryFilter(pyes.MatchQuery('command', 'js::shadow',"phrase")),
            pyes.QueryFilter(pyes.MatchQuery('command', 'target.new',"phrase")),
            pyes.QueryFilter(pyes.MatchQuery('command', '/usr/share/man',"phrase")),
            pyes.QueryFilter(pyes.MatchQuery('command', 'shadow-invert.png',"phrase")),
            pyes.QueryFilter(pyes.MatchQuery('command', 'ruby-shadow',"phrase")),
            pyes.QueryFilter(pyes.QueryStringQuery('command:gzip')),
            pyes.QueryFilter(pyes.QueryStringQuery('command:http')),
            pyes.QueryFilter(pyes.QueryStringQuery('command:html'))
        ]))
        pyesresults = es.search(q, size=1000, indices='events')
        # logger.debug(results.count())

        # correlate any matches by the dhost field.
        # make a simple list of indicator values that can be counted/summarized by Counter
        resultsIndicators = list()

        # bug in pyes..capture results as raw list or it mutates after first access:
        # copy the hits.hits list as our resusts, which is the same as the official elastic search library returns.
        results = pyesresults._search_raw()['hits']['hits']
        for r in results:
            resultsIndicators.append(r['_source']['details']['dhost'])

        # use the list of tuples ('indicator',count) to create a dictionary with:
        # indicator,count,es records
        # and add it to a list to return.
        indicatorList = list()
        for i in Counter(resultsIndicators).most_common():
            idict = dict(indicator=i[0], count=i[1], events=[])
            for r in results:
                if r['_source']['details']['dhost'].encode('ascii', 'ignore') == i[0]:
                    idict['events'].append(r)
            indicatorList.append(idict)
        return indicatorList

    except pyes.exceptions.NoServerAvailable:
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
    es = pyes.ES((list('{0}'.format(s) for s in options.esservers)))
    # run a series of searches for suspicious commands
    # aggregating by a specific field (usually dhost or suser)
    # and alert if found
    
    # /etc/shadow manipulation by destination host
    indicatorCounts = esRunSearch(es,esShadowSearch(), 'suser')
    createAlerts(es, indicatorCounts)

    # search for rpm -i or -e type commands by suser:
    indicatorCounts=esRunSearch(es,esRPMSearch(),'suser')
    createAlerts(es,indicatorCounts)
    
    # search for yum remove commands by suser:
    indicatorCounts=esRunSearch(es,esYumSearch(),'suser')
    createAlerts(es,indicatorCounts)
 
    # search for gcc commands by suser:
    indicatorCounts=esRunSearch(es,esGCCSearch(),'suser')
    createAlerts(es,indicatorCounts)

    # search for history modification commands by suser:
    indicatorCounts=esRunSearch(es,esHistoryModSearch(),'suser')
    createAlerts(es,indicatorCounts)  
    
    logger.debug('finished')


def initConfig():
    # change this to your default zone for when it's not specified
    options.defaultTimeZone = getConfig('defaulttimezone', 'UTC', options.configfile)
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
