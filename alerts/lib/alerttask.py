#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
# Copyright (c) 2017 Mozilla Corporation
#
# Contributors:
# Anthony Verez averez@mozilla.com
# Jeff Bryner jbryner@mozilla.com
# Brandon Myers bmyers@mozilla.com

import collections
import json
import kombu
import os
import sys

from configlib import getConfig, OptionParser
from datetime import datetime
from collections import Counter
from celery import Task
from celery.utils.log import get_task_logger
from config import RABBITMQ, ES

sys.path.append(os.path.join(os.path.dirname(__file__), "../../lib"))
from utilities.toUTC import toUTC
from elasticsearch_client import ElasticsearchClient
from query_models import TermMatch


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

    abstract = True

    def __init__(self):
        self.alert_name = self.__class__.__name__
        self.main_query = None

        # Used to store any alerts that were thrown
        self.alert_ids = []

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

        self.event_indices = ['events', 'events-previous']

    def classname(self):
        return self.__class__.__name__

    @property
    def log(self):
        return get_task_logger('%s.%s' % (__name__, self.alert_name))

    def parse_config(self, config_filename, config_keys):
        myparser = OptionParser()
        self.config = None
        (self.config, args) = myparser.parse_args([])
        for config_key in config_keys:
            temp_value = getConfig(config_key, '', config_filename)
            setattr(self.config, config_key, temp_value)

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
            alertQueue = kombu.Queue(RABBITMQ['alertqueue'], exchange=self.alertExchange)
            alertQueue(self.mqConn).declare()
            self.mqproducer = self.mqConn.Producer(serializer='json')
            self.log.debug('Kombu configured')
        except Exception as e:
            self.log.error('Exception while configuring kombu for alerts: {0}'.format(e))

    def _configureES(self):
        """
        Configure elasticsearch client
        """
        try:
            self.es = ElasticsearchClient(ES['servers'])
            self.log.debug('ES configured')
        except Exception as e:
            self.log.error('Exception while configuring ES for alerts: {0}'.format(e))

    def mostCommon(self, listofdicts, dictkeypath):
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
            res = self.es.save_alert(body=alertDict)
            self.log.debug('alert sent to ES')
            self.log.debug(res)
            return res
        except Exception as e:
            self.log.error('Exception while pushing alert to ES: {0}'.format(e))

    def tagBotNotify(self, alert):
        """
            Tag alert to be excluded based on severity
            If 'ircchannel' is set in an alert, we automatically notify mozdefbot
        """
        alert['notify_mozdefbot'] = True
        if alert['severity'] == 'NOTICE' or alert['severity'] == 'INFO':
            alert['notify_mozdefbot'] = False

        # If an alert sets specific ircchannel, then we should probably always notify in mozdefbot
        if 'ircchannel' in alert and alert['ircchannel'] != '' and alert['ircchannel'] != None:
            alert['notify_mozdefbot'] = True
        return alert

    def saveAlertID(self, saved_alert):
        """
        Save alert to self so we can analyze it later
        """
        self.alert_ids.append(saved_alert['_id'])

    def filtersManual(self, query):
        """
        Configure filters manually

        query is a search query object with date_timedelta populated

        """
        # Don't fire on already alerted events
        duplicate_matcher = TermMatch('alert_names', self.classname())
        if duplicate_matcher not in query.must_not:
            query.add_must_not(duplicate_matcher)

        self.main_query = query

    def searchEventsSimple(self):
        """
        Search events matching filters, store events in self.events
        """
        try:
            results = self.main_query.execute(self.es, indices=self.event_indices)
            self.events = results['hits']
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
            esresults = self.main_query.execute(self.es, indices=self.event_indices)
            results = esresults['hits']

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
                    alert = self.tagBotNotify(alert)
                    self.log.debug(alert)
                    alertResultES = self.alertToES(alert)
                    self.tagEventsAlert([i], alertResultES)
                    self.alertToMessageQueue(alert)
                    self.hookAfterInsertion(alert)
                    self.saveAlertID(alertResultES)
        # did we not match anything?
        # can also be used as an alert trigger
        if len(self.events) == 0:
            alert = self.onNoEvent(**kwargs)
            if alert:
                alert = self.tagBotNotify(alert)
                self.log.debug(alert)
                alertResultES = self.alertToES(alert)
                self.alertToMessageQueue(alert)
                self.hookAfterInsertion(alert)
                self.saveAlertID(alertResultES)


    def walkAggregations(self, threshold, config=None):
        """
        Walk through aggregations, provide some methods to hook in alerts
        """
        if len(self.aggregations) > 0:
            for aggregation in self.aggregations:
                if aggregation['count'] >= threshold:
                    aggregation['config']=config
                    alert = self.onAggregation(aggregation)
                    if alert:
                        alert = self.tagBotNotify(alert)
                        self.log.debug(alert)
                        alertResultES = self.alertToES(alert)
                        # even though we only sample events in the alert
                        # tag all events as alerted to avoid re-alerting
                        # on events we've already processed.
                        self.tagEventsAlert(aggregation['allevents'], alertResultES)
                        self.alertToMessageQueue(alert)
                        self.saveAlertID(alertResultES)


    def createAlertDict(self, summary, category, tags, events, severity='NOTICE', url=None, ircchannel=None):
        """
        Create an alert dict
        """
        alert = {
            'utctimestamp': toUTC(datetime.now()).isoformat(),
            'severity': severity,
            'summary': summary,
            'category': category,
            'tags': tags,
            'events': [],
            'ircchannel': ircchannel,
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
        and update the alert_names on the event itself so it's
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

                if 'alert_names' not in event['_source']:
                    event['_source']['alert_names'] = []
                event['_source']['alert_names'].append(self.classname())

                self.es.save_event(index=event['_index'], doc_type=event['_type'], body=event['_source'], doc_id=event['_id'])
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

    def parse_json_alert_config(self, config_file):
        """
        Helper function to parse an alert config file
        """
        alert_dir = os.path.join(os.path.dirname(__file__), '..')
        config_file_path = os.path.join(alert_dir, config_file)
        json_obj = {}
        with open(config_file_path, "r") as fd:
            try:
                json_obj = json.load(fd)
            except ValueError:
                sys.stderr.write("FAILED to open the configuration file\n")

        return json_obj
