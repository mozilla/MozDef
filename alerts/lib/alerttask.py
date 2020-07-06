#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# Copyright (c) 2017 Mozilla Corporation

import collections
import json
import kombu
import os
import socket
import netaddr

from configlib import getConfig, OptionParser
from datetime import datetime
from collections import Counter
from celery import Task
from celery.utils.log import get_task_logger

from mozdef_util.utilities.toUTC import toUTC
from mozdef_util.utilities.logger import logger
from mozdef_util.elasticsearch_client import ElasticsearchClient
from mozdef_util.query_models import TermMatch, ExistsMatch

from lib.config import RABBITMQ, ES, ALERT_PLUGINS
from lib.alert_plugin_set import AlertPluginSet


# Status set by the triage bot after a user, pinged on slack, indicates
# whether their (known) activity triggered an alert.
DEFAULT_STATUS = 'manual'


# utility functions used by AlertTask.mostCommon
# determine most common values
# in a list of dicts
def keypaths(nested):
    """ return a list of nested dict key paths
        like: [u'_source', u'details', u'program']
    """
    for key, value in nested.items():
        if isinstance(value, collections.Mapping):
            for subkey, subvalue in keypaths(value):
                yield [key] + subkey, subvalue
        else:
            yield [key], value


def dictpath(path):
    """ split a string representing a
        nested dictionary path key.subkey.subkey
    """
    for i in path.split("."):
        yield "{0}".format(i)


def getValueByPath(input_dict, path_string):
    """
        Gets data/value from a dictionary using a dotted accessor-string
        http://stackoverflow.com/a/7534478
        path_string can be key.subkey.subkey.subkey
    """
    return_data = input_dict
    for chunk in path_string.split("."):
        return_data = return_data.get(chunk, {})
    return return_data


def hostname_from_ip(ip):
    try:
        reversed_dns = socket.gethostbyaddr(ip)
        return reversed_dns[0]
    except socket.herror:
        return None


def add_hostname_to_ip(ip, output_format, require_internal=True):
    ip_obj = netaddr.IPNetwork(ip)[0]
    if require_internal and not ip_obj.is_private():
        return ip
    hostname = hostname_from_ip(ip)
    if hostname is None:
        return ip
    else:
        return output_format.format(ip, hostname)


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

        self.log.debug("starting {0}".format(self.alert_name))
        self.log.debug(RABBITMQ)
        self.log.debug(ES)

        self._configureKombu()
        self._configureES()

        self.event_indices = ['events', 'events-previous']
        plugin_dir = os.path.join(os.path.dirname(__file__), "../plugins")
        self.plugin_set = AlertPluginSet(plugin_dir, ALERT_PLUGINS)

    def classname(self):
        return self.__class__.__name__

    @property
    def log(self):
        return get_task_logger("%s.%s" % (__name__, self.alert_name))

    def parse_config(self, config_filename, config_keys):
        myparser = OptionParser()
        self.config = None
        (self.config, args) = myparser.parse_args([])
        full_config_filename = os.path.join(os.path.dirname(__file__), "../", config_filename)
        for config_key in config_keys:
            temp_value = getConfig(config_key, "", full_config_filename)
            setattr(self.config, config_key, temp_value)

    def close_connections(self):
        self.mqConn.release()

    def _discover_task_exchange(self):
        """Use configuration information to understand the message queue protocol.
        return: amqp, sqs
        """
        return getConfig("mqprotocol", "amqp", None)

    def __build_conn_string(self):
        exchange_protocol = self._discover_task_exchange()
        if exchange_protocol == "amqp":
            connString = "amqp://{0}:{1}@{2}:{3}//".format(
                RABBITMQ["mquser"],
                RABBITMQ["mqpassword"],
                RABBITMQ["mqserver"],
                RABBITMQ["mqport"],
            )
            return connString
        elif exchange_protocol == "sqs":
            connString = "sqs://{}".format(getConfig("alertSqsQueueUrl", None, None))
            if connString:
                connString = connString.replace('https://','')
            return connString

    def _configureKombu(self):
        """
        Configure kombu for amqp or sqs
        """
        try:
            connString = self.__build_conn_string()
            self.mqConn = kombu.Connection(connString)
            if connString.find('sqs') == 0:
                self.mqConn.transport_options['region'] = os.getenv('DEFAULT_AWS_REGION', 'us-west-2')
                self.mqConn.transport_options['is_secure'] = True
                self.alertExchange = kombu.Exchange(
                    name=RABBITMQ["alertexchange"], type="topic", durable=True
                )
                self.alertExchange(self.mqConn).declare()
                alertQueue = kombu.Queue(
                    os.getenv('OPTIONS_ALERTSQSQUEUEURL').split('/')[4], exchange=self.alertExchange
                )
            else:
                self.alertExchange = kombu.Exchange(
                    name=RABBITMQ["alertexchange"], type="topic", durable=True
                )
                self.alertExchange(self.mqConn).declare()
                alertQueue = kombu.Queue(
                    RABBITMQ["alertqueue"], exchange=self.alertExchange
                )
            alertQueue(self.mqConn).declare()
            self.mqproducer = self.mqConn.Producer(serializer="json")
            self.log.debug("Kombu configured")
        except Exception as e:
            self.log.error(
                "Exception while configuring kombu for alerts: {0}".format(e)
            )

    def _configureES(self):
        """
        Configure elasticsearch client
        """
        try:
            self.es = ElasticsearchClient(ES["servers"])
            self.log.debug("ES configured")
        except Exception as e:
            self.log.error("Exception while configuring ES for alerts: {0}".format(e))

    def mostCommon(self, listofdicts, dictkeypath):
        """
            Given a list containing dictionaries,
            return the most common entries
            along a key path separated by .
            i.e. dictkey.subkey.subkey
            returned as a list of tuples
            [(value,count),(value,count)]
        """
        inspectlist = list()
        path = list(dictpath(dictkeypath))
        for i in listofdicts:
            for k in list(keypaths(i)):
                if not (set(k[0]).symmetric_difference(path)):
                    inspectlist.append(k[1])

        return Counter(inspectlist).most_common()

    def alertToMessageQueue(self, alertDict):
        """
        Send alert to the kombu based message queue.  The default is rabbitmq.
        """
        try:
            self.log.debug(alertDict)
            ensurePublish = self.mqConn.ensure(
                self.mqproducer, self.mqproducer.publish, max_retries=10
            )
            ensurePublish(
                alertDict,
                exchange=self.alertExchange,
                routing_key=RABBITMQ["alertqueue"],
            )
            self.log.debug("alert sent to the alert queue")
        except Exception as e:
            self.log.error(
                "Exception while sending alert to message queue: {0}".format(e)
            )

    def alertToES(self, alertDict):
        """
        Send alert to elasticsearch
        """
        try:
            res = self.es.save_alert(body=alertDict)
            self.log.debug("alert sent to ES")
            self.log.debug(res)
            return res
        except Exception as e:
            self.log.error("Exception while pushing alert to ES: {0}".format(e))

    def tagBotNotify(self, alert):
        """
            Tag alert to be excluded based on severity
            If 'channel' is set in an alert, we automatically notify mozdefbot
        """
        # If an alert code hasn't explicitly set notify_mozdefbot field
        if 'notify_mozdefbot' not in alert or alert['notify_mozdefbot'] is None:
            alert["notify_mozdefbot"] = True
            if alert["severity"] == "NOTICE" or alert["severity"] == "INFO":
                alert["notify_mozdefbot"] = False

            # If an alert sets specific channel, then we should probably always notify in mozdefbot
            if (
                "channel" in alert and alert["channel"] != "" and alert["channel"] is not None
            ):
                alert["notify_mozdefbot"] = True
        return alert

    def saveAlertID(self, saved_alert):
        """
        Save alert to self so we can analyze it later
        """
        self.alert_ids.append(saved_alert["_id"])

    def filtersManual(self, query):
        """
        Configure filters manually

        query is a search query object with date_timedelta populated

        """
        # Don't fire on already alerted events
        duplicate_matcher = TermMatch("alert_names", self.determine_alert_classname())
        if duplicate_matcher not in query.must_not:
            query.add_must_not(duplicate_matcher)

        self.main_query = query

    def determine_alert_classname(self):
        alert_name = self.classname()
        # Allow alerts like the generic alerts (one python alert but represents many 'alerts')
        # can customize the alert name
        if hasattr(self, "custom_alert_name"):
            alert_name = self.custom_alert_name
        return alert_name

    def executeSearchEventsSimple(self):
        """
        Execute the search for simple events
        """
        return self.main_query.execute(self.es, indices=self.event_indices)

    def searchEventsSimple(self):
        """
        Search events matching filters, store events in self.events
        """
        try:
            results = self.executeSearchEventsSimple()
            self.events = results["hits"]
            self.log.debug(self.events)
        except Exception as e:
            self.log.error("Error while searching events in ES: {0}".format(e))

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

        # We automatically add the key that we're matching on
        # for aggregation, as a query requirement
        aggreg_key_exists = ExistsMatch(aggregationPath)
        if aggreg_key_exists not in self.main_query.must:
            self.main_query.add_must(aggreg_key_exists)

        try:
            esresults = self.main_query.execute(self.es, indices=self.event_indices)
            results = esresults["hits"]

            # List of aggregation values that can be counted/summarized by Counter
            # Example: ['evil@evil.com','haxoor@noob.com', 'evil@evil.com'] for an email aggregField
            aggregationValues = []
            for r in results:
                aggregationValues.append(getValueByPath(r["_source"], aggregationPath))

            # [{value:'evil@evil.com',count:1337,events:[...]}, ...]
            aggregationList = []
            for i in Counter(aggregationValues).most_common():
                idict = {"value": i[0], "count": i[1], "events": [], "allevents": []}
                for r in results:
                    if getValueByPath(r["_source"], aggregationPath) == i[0]:
                        # copy events detail into this aggregation up to our samples limit
                        if len(idict["events"]) < samplesLimit:
                            idict["events"].append(r)
                        # also copy all events to a non-sampled list
                        # so we mark all events as alerted and don't re-alert
                        idict["allevents"].append(r)
                aggregationList.append(idict)

            self.aggregations = aggregationList
            self.log.debug(self.aggregations)
        except Exception as e:
            self.log.error("Error while searching events in ES: {0}".format(e))

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
                    alert = self.alertPlugins(alert)
                    alertResultES = self.alertToES(alert)
                    self.tagEventsAlert([i], alertResultES)
                    full_alert_doc = self.generate_full_doc(alert, alertResultES)
                    self.alertToMessageQueue(full_alert_doc)
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
                full_alert_doc = self.generate_full_doc(alert, alertResultES)
                self.alertToMessageQueue(full_alert_doc)
                self.hookAfterInsertion(alert)
                self.saveAlertID(alertResultES)

    def walkAggregations(self, threshold, config=None):
        """
        Walk through aggregations, provide some methods to hook in alerts
        """
        if len(self.aggregations) > 0:
            for aggregation in self.aggregations:
                if aggregation["count"] >= threshold:
                    aggregation["config"] = config
                    alert = self.onAggregation(aggregation)
                    if alert:
                        alert = self.tagBotNotify(alert)
                        self.log.debug(alert)
                        alert = self.alertPlugins(alert)
                        alertResultES = self.alertToES(alert)
                        full_alert_doc = self.generate_full_doc(alert, alertResultES)
                        # even though we only sample events in the alert
                        # tag all events as alerted to avoid re-alerting
                        # on events we've already processed.
                        self.tagEventsAlert(aggregation["allevents"], alertResultES)
                        self.alertToMessageQueue(full_alert_doc)
                        self.saveAlertID(alertResultES)

    def alertPlugins(self, alert):
        """
        Send alerts through a plugin system
        """
        alertDict = self.plugin_set.run_plugins(alert)[0]

        return alertDict

    def createAlertDict(
        self,
        summary,
        category,
        tags,
        events,
        severity="NOTICE",
        url=None,
        channel=None,
        notify_mozdefbot=None,
    ):
        """
        Create an alert dict
        """

        # Tag alert documents with alert classname
        # that was triggered
        classname = self.__name__
        # Handle generic alerts
        if classname == 'AlertGenericLoader':
            classname = self.custom_alert_name

        alert = {
            "utctimestamp": toUTC(datetime.now()).isoformat(),
            "severity": severity,
            "summary": summary,
            "category": category,
            "tags": tags,
            "events": [],
            "channel": channel,
            "notify_mozdefbot": notify_mozdefbot,
            "status": DEFAULT_STATUS,
            "classname": classname
        }
        if url:
            alert["url"] = url

        for e in events:
            alert["events"].append(
                {
                    "documentindex": e["_index"],
                    "documentsource": e["_source"],
                    "documentid": e["_id"],
                }
            )
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
                if "alerts" not in event["_source"]:
                    event["_source"]["alerts"] = []
                event["_source"]["alerts"].append(
                    {"index": alertResultES["_index"], "id": alertResultES["_id"]}
                )

                if "alert_names" not in event["_source"]:
                    event["_source"]["alert_names"] = []
                event["_source"]["alert_names"].append(self.determine_alert_classname())

                self.es.save_event(index=event["_index"], body=event["_source"], doc_id=event["_id"])
                # We refresh here to ensure our changes to the events will show up for the next search query results
                self.es.refresh(event["_index"])
        except Exception as e:
            self.log.error("Error while updating events in ES: {0}".format(e))

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
            self.log.debug("finished")
        except Exception as e:
            self.error_thrown = e
            self.log.exception("Exception in main() method: {0}".format(e))

    def parse_json_alert_config(self, config_file):
        """
        Helper function to parse an alert config file
        """
        alert_dir = os.path.join(os.path.dirname(__file__), "..")
        config_file_path = os.path.abspath(os.path.join(alert_dir, config_file))
        json_obj = {}
        with open(config_file_path, "r") as fd:
            try:
                json_obj = json.load(fd)
            except ValueError:
                logger.error("FAILED to open the configuration file\n")

        return json_obj

    def generate_full_doc(self, alert_body, alert_es):
        return {
            '_id': alert_es['_id'],
            '_index': alert_es['_index'],
            '_source': alert_body
        }
