#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
# Copyright (c) 2014 Mozilla Corporation
#
# Contributors:
# Anthony Verez averez@mozilla.com

from datetime import datetime
from datetime import timedelta
from collections import Counter
import json

from celery import Task
from celery.utils.log import get_task_logger

import kombu
import pyes

from config import RABBITMQ, ES

class AlertTask(Task):

    def __init__(self):
        self.alert_name = self.__class__.__name__
        self.filter = None
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
                type='direct',
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
                routing_key=RABBITMQ['alertexchange'])
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
        begindateUTC = datetime.utcnow() - timedelta(**date_timedelta)
        enddateUTC = datetime.utcnow()
        qDate = pyes.RangeQuery(qrange=pyes.ESRange('utctimestamp',
            from_value=begindateUTC, to_value=enddateUTC))
        q = pyes.ConstantScoreQuery(pyes.MatchAllQuery())
        must_not.append(pyes.ExistsFilter('alerttimestamp'))
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

    def searchEventsAggreg(self, aggregField, samplesLimit=5):
        """
        Search aggregations matching filters by aggregField, store them in self.aggregations
        """
        try:
            pyesresults = self.es.search(
                self.filter,
                size=1000,
                indices='events,events-previous')
            results = pyesresults._search_raw()['hits']['hits']

            # List of aggregation values that can be counted/summarized by Counter
            # Example: ['evil@evil.com','haxoor@noob.com', 'evil@evil.com'] for an email aggregField
            aggregValues = []
            for r in results:
                aggregValues.append(r['_source']['details'][aggregField])

            # [{value:'evil@evil.com',count:1337,events:[...]}, ...]
            aggregList = []
            for i in Counter(aggregValues).most_common():
                idict = {
                    'value': i[0],
                    'count': i[1],
                    'events': []
                }
                for r in results:
                    if r['_source']['details'][aggregField].encode('ascii', 'ignore') == i[0]:
                        # copy events detail into this aggregation up to our samples limit
                        if len(idict['events']) < samplesLimit:
                            idict['events'].append(r)
                aggregList.append(idict)

            self.aggregations = aggregList
            self.log.debug(self.aggregations)
        except Exception as e:
            self.log.error('Error while searching events in ES: {0}'.format(e))

    def walkEvents(self):
        """
        Walk through events, provide some methods to hook in alerts
        """
        if len(self.events) > 0:
            for i in self.events:
                alert = self.onEvent(i)
                if alert:
                    self.log.debug(alert)
                    alertResultES = self.alertToES(alert)
                    self.tagEventsAlert([i], alertResultES)
                    self.alertToMessageQueue(alert)
                    self.hookAfterInsertion(alert)

    def walkAggregations(self, threshold):
        """
        Walk through aggregations, provide some methods to hook in alerts
        """
        if len(self.aggregations) > 0:
            for aggreg in self.aggregations:
                if aggreg['count'] >= threshold:
                    alert = self.onAggreg(aggreg)
                    self.log.debug(alert)
                    if alert:
                        alertResultES = self.alertToES(alert)
                        self.tagEventsAlert(aggreg['events'], alertResultES)
                        self.alertToMessageQueue(alert)

    def createAlertDict(self, summary, category, tags, events, severity='NOTICE'):
        """
        Create an alert dict
        """
        alert = {
            'utctimestamp': datetime.utcnow().isoformat(),
            'severity': severity,
            'summary': summary,
            'category': category,
            'tags': tags,
            'events': []
        }
        for e in events:
            alert['events'].append({
                'documentindex': e['_index'],
                'documenttype': e['_type'],
                'documentsource': e['_source'],
                'documentid': e['_id']})
        self.log.debug(alert)
        return alert

    def onEvent(self, event):
        """
        To be overriden by children to run their code
        to be used when creating an alert using an event
        must return an alert dict or None
        """
        pass

    def onAggreg(self, aggreg):
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
                event['_source']['alerttimestamp'] = datetime.utcnow().isoformat()

                self.es.update(event['_index'], event['_type'],
                    event['_id'], document=event['_source'])
        except Exception as e:
            self.log.error('Error while updating events in ES: {0}'.format(e))

    def main(self):
        """
        To be overriden by children to run their code
        """
        pass

    def run(self):
        """
        Main method launched by celery periodically
        """
        try:
            self.main()
            self.log.debug('finished')
        except Exception as e:
            self.log.error('Exception in main() method: {0}'.format(e))
