#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
# Copyright (c) 2017 Mozilla Corporation

# Check if projectID has been defined in the config
# Check if subscriptionName has been defined in the config
# Write a message handler -> ACK and process the message (but wrap processing in a try/catch)
# Check if the message's fields + metadata are present and of a correct type - https://github.com/mozilla/fxa/blob/master/packages/fxa-customs-server/lib/dataflow.js#L130
# See https://docs.google.com/document/d/1ESuraiNM5nPlicQ5zLFwOYZktTV-i8tqwbnwmxdJzyk
# for expected metadata fields
# Catch https://googleapis.dev/python/pubsub/latest/subscriber/api/futures.html#google.cloud.pubsub_v1.subscriber.futures.StreamingPullFuture
# Set the flow_control in the subscribe(subscription, callback, flow_control=(), scheduler=None) call
# https://github.com/GoogleCloudPlatform/python-docs-samples/blob/master/pubsub/cloud-client/subscriber.py
# https://github.com/mozilla/fxa/blob/master/packages/fxa-customs-server/lib/dataflow.js#L155
# Admin Activity audit logs
# Data Access audit logs
# System Event audit logs
# https://cloud.google.com/logging/docs/reference/v2/rest/v2/LogEntry

import json

import sys
import os
import socket
import time
import pytz
import time
from configlib import getConfig, OptionParser
from datetime import datetime
from mozdef_util.utilities.toUTC import toUTC
from mozdef_util.utilities.logger import logger, initLogger
from mozdef_util.elasticsearch_client import (
    ElasticsearchClient,
    ElasticsearchBadServer,
    ElasticsearchInvalidIndex,
    ElasticsearchException,
)
from google.cloud import pubsub

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../"))
from mq.lib.plugins import sendEventToPlugins, registerPlugins
from mq.lib.sqs import connect_sqs

# running under uwsgi?
try:
    import uwsgi

    hasUWSGI = True
except ImportError as e:
    hasUWSGI = False


class PubSubtaskConsumer(object):
    def __init__(self, esConnection, options):
        self.esConnection = esConnection
        self.pluginList = registerPlugins()
        self.options = options
        self.scopes = [
            "https://www.googleapis.com/auth/cloud-platform",
            "https://www.googleapis.com/auth/pubsub ",
        ]
        self.credentials_file = options.credentials_file

    def run(self):
        subscriber = pubsub.SubscriberClient()
        res = subscriber.subscribe(self.options.resource_name, callback=self.onMessage)
        try:
            res.result()
        except Exception as ex:
            # res.close()
            raise

    def onMessage(self, message):
        message_json = json.loads(message.data.decode("UTF-8"))
        try:
            # default elastic search metadata for an event
            metadata = {"index": "events", "id": None}
            event = {}

            event["receivedtimestamp"] = toUTC(datetime.now()).isoformat()
            event["mozdefhostname"] = self.options.mozdefhostname

            if "tags" in event:
                event["tags"].extend([self.options.resource_name])
            else:
                event["tags"] = [self.options.resource_name]
            event["tags"].extend(["pubsub"])

            event["details"] = json.loads(message.data.decode("UTF-8"))
            (event, metadata) = sendEventToPlugins(event, metadata, self.pluginList)
            # Drop message if plugins set to None
            if event is None:
                message.ack()
                return
            self.save_event(event, metadata)
            message.ack()
        except Exception as e:
            logger.exception(e)
            logger.error("Malformed message: %r" % message)
            message.ack()

    def save_event(self, event, metadata):
        try:
            # drop the message if a plug in set it to None
            # signaling a discard
            if event is None:
                return

            # make a json version for posting to elastic search
            jbody = json.JSONEncoder().encode(event)

            try:
                bulk = False
                if self.options.esbulksize != 0:
                    bulk = True

                self.esConnection.save_event(
                    index=metadata["index"],
                    doc_id=metadata["id"],
                    body=jbody,
                    bulk=bulk,
                )

            except (ElasticsearchBadServer, ElasticsearchInvalidIndex) as e:
                # handle loss of server or race condition with index rotation/creation/aliasing
                try:
                    self.esConnection = esConnect()
                    return
                # XXX: ain't no kombu here but maybe pubsub errors?
                except kombu.exceptions.MessageStateError:
                    return
            except ElasticsearchException as e:
                logger.exception(
                    "ElasticSearchException: {0} reported while indexing event".format(
                        e
                    )
                )
                logger.error("Malformed jbody: %r" % jbody)
                return
        except Exception as e:
            logger.exception(e)
            logger.error("Malformed message: %r" % event)


def esConnect():
    """open or re-open a connection to elastic search"""
    return ElasticsearchClient(
        (list("{0}".format(s) for s in options.esservers)), options.esbulksize
    )


def initConfig():
    # capture the hostname
    options.mozdefhostname = getConfig(
        "mozdefhostname", socket.gethostname(), options.configfile
    )

    # elastic search options. set esbulksize to a non-zero value to enable bulk posting, set timeout to post no matter how many events after X seconds.
    options.esservers = list(
        getConfig("esservers", "http://localhost:9200", options.configfile).split(",")
    )
    options.esbulksize = getConfig("esbulksize", 0, options.configfile)
    options.esbulktimeout = getConfig("esbulktimeout", 30, options.configfile)

    # XXX: change it to the GCP threshold and make it optional
    options.prefetch = getConfig("prefetch", 10, options.configfile)

    # GCP PubSub options
    options.resource_name = getConfig("resource_name", "", options.configfile)
    options.credentials_file = getConfig("credentials_file", "", options.configfile)

    options.mqprotocol = getConfig("mqprotocol", "pubsub", options.configfile)

    # plugin options
    # secs to pass before checking for new/updated plugins
    # seems to cause memory leaks..
    # regular updates are disabled for now,
    # though we set the frequency anyway.
    options.plugincheckfrequency = getConfig(
        "plugincheckfrequency", 120, options.configfile
    )


def main():
    if hasUWSGI:
        logger.info("started as uwsgi mule {0}".format(uwsgi.mule_id()))
    else:
        logger.info("started without uwsgi")

    if options.mqprotocol not in ("pubsub"):
        logger.error("Can only process pubsub queues, terminating")
        sys.exit(1)

    # connect to GCP and consume our queue
    PubSubtaskConsumer(es, options).run()


if __name__ == "__main__":
    # configure ourselves
    parser = OptionParser()
    parser.add_option(
        "-c",
        dest="configfile",
        default=sys.argv[0].replace(".py", ".conf"),
        help="configuration file to use",
    )
    (options, args) = parser.parse_args()
    initConfig()
    initLogger(options)

    # open ES connection globally so we don't waste time opening it per message
    es = esConnect()

    main()
    try:
        main()
    except KeyboardInterrupt as e:
        logger.info("Exiting worker")
        if options.esbulksize != 0:
            es.finish_bulk()
    except Exception as e:
        if options.esbulksize != 0:
            es.finish_bulk()
        raise

