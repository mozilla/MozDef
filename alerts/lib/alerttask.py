#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
# Copyright (c) 2014 Mozilla Corporation
#
# Contributors:
# Anthony Verez averez@mozilla.com
# Jeff Bryner jbryner@mozilla.com

import collections
import json
import kombu
import pytz
import pyes

from datetime import datetime
from datetime import timedelta
from dateutil.parser import parse
from collections import Counter
from celery import Task
from celery.utils.log import get_task_logger
from config import RABBITMQ, ES, OPTIONS

def toUTC(suspectedDate, localTimeZone=None):
    '''make a UTC date out of almost anything'''
    utc = pytz.UTC
    objDate = None
    if localTimeZone is None:
        localTimeZone= OPTIONS['defaulttimezone']
    if type(suspectedDate) in (str, unicode):
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


# utility functions used by AlertTask.mostCommon
# determine most common values
# in a list of dicts
def keypaths(nested):
    ''' return a list of nested dict key paths
        like: [u'_source', u'details', u'hostname']
    '''
    for key, value in nested.iteritems():
        if isinstance(value, collections.Mapping):
            for subkey, subvalue in keypaths(value):
                yield [key] + subkey, subvalue
        else:
            yield [key], value


def dictpath(path):
    ''' split a string representing a
        nested dictionary path key.subkey.subkey
    '''
    for i in path.split('.'):
        yield '{0}'.format(i)


def getValueByPath(input_dict, path_string):
    """
        Gets data/value from a dictionary using a dotted accessor-string
        http://stackoverflow.com/a/7534478
        path_string can be key.subkey.subkey.subkey
    """
    return_data = input_dict
    for chunk in path_string.split('.'):
        return_data = return_data.get(chunk, {})
    return return_data


class AlertTask(Task):

    def __init__(self):
        self.alert_name = self.__class__.__name__
        self.filter = None
        self.begindateUTC = None
        self.enddateUTC = None
        # List of events
        self.events = None
        # List of aggregations
        # e.g. when aggregField is email: [{value:'evil@evil.com',count:1337,events:[...]}, ...]
        self.aggregations = None

        self.log.debug('starting {0}'.format(self.alert_name))
        self.log.debug(RABBITMQ)
        self.log.debug(ES)

        self._configureKombu()
        self._configureES()

    @property
    def log(self):
        return get_task_logger('%s.%s' % (__name__, self.alert_name))

    def _configureKombu(self):
        """
        Configure kombu for rabbitmq
        """
        try:
            connString = 'amqp://{0}:{1}@{2}:{3}//'.format(
                RABBITMQ['mquser'],
                RABBITMQ['mqpassword'],
                RABBITMQ['mqserver'],
                RABBITMQ['mqport'])
            self.mqConn = kombu.Connection(connString)

            self.alertExchange = kombu.Exchange(
                name=RABBITMQ['alertexchange'],
                type='topic',
                durable=True)
            self.alertExchange(self.mqConn).declare()
            alertQueue = kombu.Queue(RABBITMQ['alertqueue'],
                exchange=self.alertExchange)
            alertQueue(self.mqConn).declare()
            self.mqproducer = self.mqConn.Producer(serializer='json')
            self.log.debug('Kombu configured')
        except Exception as e:
            self.log.error('Exception while configuring kombu for alerts: {0}'.format(e))


    def _configureES(self):
        """
        Configure pyes for elasticsearch
        """
        try:
            self.es = pyes.ES(ES['servers'])
            self.log.debug('ES configured')
        except Exception as e:
            self.log.error('Exception while configuring ES for alerts: {0}'.format(e))


    def mostCommon(self, listofdicts,dictkeypath):
        """
            Given a list containing dictionaries,
            return the most common entries
            along a key path separated by .
            i.e. dictkey.subkey.subkey
            returned as a list of tuples
            [(value,count),(value,count)]
        """
        inspectlist=list()
        path=list(dictpath(dictkeypath))
        for i in listofdicts:
            for k in list(keypaths(i)):
                if not (set(k[0]).symmetric_difference(path)):
                    inspectlist.append(k[1])

        return Counter(inspectlist).most_common()


    def alertToMessageQueue(self, alertDict):
        """
        Send alert to the rabbit message queue
        """
        try:
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
            self.log.debug(mqAlert)
            ensurePublish = self.mqConn.ensure(
                self.mqproducer,
                self.mqproducer.publish,
                max_retries=10)
            ensurePublish(alertDict,
                exchange=self.alertExchange,
                routing_key=RABBITMQ['alertqueue'])
            self.log.debug('alert sent to the alert queue')
        except Exception as e:
            self.log.error('Exception while sending alert to message queue: {0}'.format(e))


    def alertToES(self, alertDict):
        """
        Send alert to elasticsearch
        """
        try:
            res = self.es.index(index='alerts', doc_type='alert', doc=alertDict)
            self.log.debug('alert sent to ES')
            self.log.debug(res)
            return res
        except Exception as e:
            self.log.error('Exception while pushing alert to ES: {0}'.format(e))


    def filtersManual(self, date_timedelta, must=[], should=[], must_not=[]):
        """
        Configure filters manually

        date_timedelta is a dict in timedelta format
        see https://docs.python.org/2/library/datetime.html#timedelta-objects

        must, should and must_not are pyes filter objects lists
        see http://pyes.readthedocs.org/en/latest/references/pyes.filters.html


        """
        self.begindateUTC = toUTC(datetime.now() - timedelta(**date_timedelta))
        self.enddateUTC = toUTC(datetime.now())
        qDate = pyes.RangeQuery(qrange=pyes.ESRange('utctimestamp',
            from_value=self.begindateUTC, to_value=self.enddateUTC))
        q = pyes.ConstantScoreQuery(pyes.MatchAllQuery())

        #Don't fire on already alerted events
        if pyes.ExistsFilter('alerttimestamp') not in must_not:
            must_not.append(pyes.ExistsFilter('alerttimestamp'))

        must.append(qDate)
        q.filters.append(pyes.BoolFilter(
            must=must,
            should=should,
            must_not=must_not))
        self.filter = q


    def filtersFromKibanaDash(self, fp, date_timedelta):
        """
        Import filters from a kibana dashboard

        fp is the file path of the json file

        date_timedelta is a dict in timedelta format
        see https://docs.python.org/2/library/datetime.html#timedelta-objects
        """
        f = open(fp)
        data = json.load(f)
        must = []
        should = []
        must_not = []
        for filtid in data['services']['filter']['list'].keys():
            filt = data['services']['filter']['list'][filtid]
            if filt['active'] and 'query' in filt.keys():
                value = filt['query'].split(':')[-1]
                fieldname = filt['query'].split(':')[0].split('.')[-1]
                # self.log.info(fieldname)
                # self.log.info(value)

                # field: fieldname
                # query: value
                if 'field' in filt.keys():
                    fieldname = filt['field']
                    value = filt['query']
                    if '\"' in value:
                        value = value.split('\"')[1]
                        pyesfilt = pyes.QueryFilter(pyes.MatchQuery(fieldname, value, 'phrase'))
                    else:
                        pyesfilt = pyes.TermFilter(fieldname, value)
                else:
                    # _exists_:field
                    if filt['query'].startswith('_exists_:'):
                        pyesfilt = pyes.ExistsFilter(value.split('.')[-1])
                        # self.log.info('exists %s' % value.split('.')[-1])
                    # _missing_:field
                    elif filt['query'].startswith('_missing_:'):
                        pyesfilt = pyes.filters.MissingFilter(value.split('.')[-1])
                        # self.log.info('missing %s' % value.split('.')[-1])
                    # field:"value"
                    elif '\"' in value:
                        value = value.split('\"')[1]
                        pyesfilt = pyes.QueryFilter(pyes.MatchQuery(fieldname, value, 'phrase'))
                        # self.log.info("phrase %s %s" % (fieldname, value))
                    # field:(value1 value2 value3)
                    elif '(' in value and ')' in value:
                        value = value.split('(')[1]
                        value = value.split('(')[0]
                        pyesfilt = pyes.QueryFilter(pyes.MatchQuery(fieldname, value, "boolean"))
                    # field:value
                    else:
                        pyesfilt = pyes.TermFilter(fieldname, value)
                        # self.log.info("terms %s %s" % (fieldname, value))

                if filt['mandate'] == 'must':
                    must.append(pyesfilt)
                elif filt['mandate'] == 'either':
                    should.append(pyesfilt)
                elif filt['mandate'] == 'mustNot':
                    must_not.append(pyesfilt)
        # self.log.info(must)
        f.close()
        self.filtersManual(date_timedelta, must=must, should=should, must_not=must_not)


    def searchEventsSimple(self):
        """
        Search events matching filters, store events in self.events
        """
        try:
            pyesresults = self.es.search(
                self.filter,
                size=1000,
                indices='events,events-previous')
            self.events = pyesresults._search_raw()['hits']['hits']
            self.log.debug(self.events)
        except Exception as e:
            self.log.error('Error while searching events in ES: {0}'.format(e))


    def searchEventsAggregated(self, aggregationPath, samplesLimit=5):
        """
        Search events, aggregate matching ES filters by aggregationPath,
        store them in self.aggregations as a list of dictionaries
        keys:
          value: the text value that was found in the aggregationPath
          count: the hitcount of the text value
          events: the sampled list of events that matched
          allevents: the unsample, total list of matching events

        aggregationPath can be key.subkey.subkey to specify a path to a dictionary value
        relative to the _source that's returned from elastic search.
        ex: details.sourceipaddress

        """
        try:
            pyesresults = self.es.search(
                self.filter,
                size=1000,
                indices='events,events-previous')
            results = pyesresults._search_raw()['hits']['hits']

            # List of aggregation values that can be counted/summarized by Counter
            # Example: ['evil@evil.com','haxoor@noob.com', 'evil@evil.com'] for an email aggregField
            aggregationValues = []
            for r in results:
                aggregationValues.append(getValueByPath(r['_source'], aggregationPath))


            # [{value:'evil@evil.com',count:1337,events:[...]}, ...]
            aggregationList = []
            for i in Counter(aggregationValues).most_common():
                idict = {
                    'value': i[0],
                    'count': i[1],
                    'events': [],
                    'allevents': []
                }
                for r in results:
                    if getValueByPath(r['_source'], aggregationPath).encode('ascii', 'ignore') == i[0]:
                        # copy events detail into this aggregation up to our samples limit
                        if len(idict['events']) < samplesLimit:
                            idict['events'].append(r)
                        # also copy all events to a non-sampled list
                        # so we mark all events as alerted and don't re-alert
                        idict['allevents'].append(r)
                aggregationList.append(idict)

            self.aggregations = aggregationList
            self.log.debug(self.aggregations)
        except Exception as e:
            self.log.error('Error while searching events in ES: {0}'.format(e))


    def walkEvents(self, **kwargs):
        """
        Walk through events, provide some methods to hook in alerts
        """
        if len(self.events) > 0:
            for i in self.events:
                alert = self.onEvent(i, **kwargs)
                if alert:
                    self.log.debug(alert)
                    alertResultES = self.alertToES(alert)
                    self.tagEventsAlert([i], alertResultES)
                    self.alertToMessageQueue(alert)
                    self.hookAfterInsertion(alert)
        # did we not match anything?
        # can also be used as an alert trigger
        if len(self.events) == 0:
            alert = self.onNoEvent(**kwargs)
            if alert:
                self.log.debug(alert)
                alertResultES = self.alertToES(alert)
                self.alertToMessageQueue(alert)
                self.hookAfterInsertion(alert)


    def walkAggregations(self, threshold):
        """
        Walk through aggregations, provide some methods to hook in alerts
        """
        if len(self.aggregations) > 0:
            for aggregation in self.aggregations:
                if aggregation['count'] >= threshold:
                    alert = self.onAggregation(aggregation)
                    self.log.debug(alert)
                    if alert:
                        alertResultES = self.alertToES(alert)
                        # even though we only sample events in the alert
                        # tag all events as alerted to avoid re-alerting
                        # on events we've already processed.
                        self.tagEventsAlert(aggregation['allevents'], alertResultES)
                        self.alertToMessageQueue(alert)


    def createAlertDict(self, summary, category, tags, events, severity='NOTICE', url=None):
        """
        Create an alert dict
        """
        alert = {
            'utctimestamp': toUTC(datetime.now()).isoformat(),
            'severity': severity,
            'summary': summary,
            'category': category,
            'tags': tags,
            'events': []
        }
        if url:
            alert['url'] = url

        for e in events:
            alert['events'].append({
                'documentindex': e['_index'],
                'documenttype': e['_type'],
                'documentsource': e['_source'],
                'documentid': e['_id']})
        self.log.debug(alert)
        return alert


    def onEvent(self, event, *args, **kwargs):
        """
        To be overriden by children to run their code
        to be used when creating an alert using an event
        must return an alert dict or None
        """
        pass


    def onNoEvent(self, *args, **kwargs):
        """
        To be overriden by children to run their code
        when NOTHING matches a filter
        which can be used to trigger on the absence of
        events much like a dead man switch.
        This is to be used when creating an alert using an event
        must return an alert dict or None
        """
        pass

    def onAggregation(self, aggregation):
        """
        To be overriden by children to run their code
        to be used when creating an alert using an aggregation
        must return an alert dict or None
        """
        pass


    def hookAfterInsertion(self, alert):
        """
        To be overriden by children to run their code
        to be used when creating an alert using an aggregation
        """
        pass


    def tagEventsAlert(self, events, alertResultES):
        """
        Update the event with the alertid/index
        and update the alerttimestamp on the event itself so it's
        not re-alerted
        """
        try:
            for event in events:
                if 'alerts' not in event['_source'].keys():
                    event['_source']['alerts'] = []
                event['_source']['alerts'].append({
                    'index': alertResultES['_index'],
                    'type': alertResultES['_type'],
                    'id': alertResultES['_id']})
                event['_source']['alerttimestamp'] = toUTC(datetime.now()).isoformat()


                self.es.update(event['_index'], event['_type'],
                    event['_id'], document=event['_source'])
        except Exception as e:
            self.log.error('Error while updating events in ES: {0}'.format(e))


    def main(self):
        """
        To be overriden by children to run their code
        """
        pass


    def run(self, *args, **kwargs):
        """
        Main method launched by celery periodically
        """
        try:
            self.main(*args, **kwargs)
            self.log.debug('finished')
        except Exception as e:
            self.log.error('Exception in main() method: {0}'.format(e))
