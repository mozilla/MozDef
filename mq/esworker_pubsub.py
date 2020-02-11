#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
# Copyright (c) 2017 Mozilla Corporation

import json
import sys
import socket
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
from lib.plugins import sendEventToPlugins, registerPlugins

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
        self.scopes = ["https://www.googleapis.com/auth/cloud-platform", "https://www.googleapis.com/auth/pubsub "]
        self.credentials_file = options.credentials_file

    def run(self):
        # XXX: fetch from the config file
        subscriber = pubsub.SubscriberClient.from_service_account_file(self.options.credentials_file)
        res = subscriber.subscribe(self.options.resource_name, callback=self.onMessage)
        try:
            res.result()
        except Exception as e:
            logger.exception(e)
            logger.error(
                "Received error during subscribing - killing self and my background thread in 5 seconds for uwsgi to bring me back"
            )
            time.sleep(5)
            res.cancel()
            sys.exit(1)

    def onMessage(self, message):
        try:
            # default elastic search metadata for an event
            metadata = {"index": "events", "id": None}
            event = {}

            event["receivedtimestamp"] = toUTC(datetime.now()).isoformat()
            event["mozdefhostname"] = self.options.mozdefhostname

            event["details"] = json.loads(message.data.decode("UTF-8"))

            if "tags" in event["details"]:
                event["tags"] = event["details"]["tags"].extend([self.options.resource_name])
            else:
                event["tags"] = [self.options.resource_name]
            event["tags"].extend(["pubsub"])

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

                self.esConnection.save_event(index=metadata["index"], doc_id=metadata["id"], body=jbody, bulk=bulk)

            except (ElasticsearchBadServer, ElasticsearchInvalidIndex) as e:
                # handle loss of server or race condition with index rotation/creation/aliasing
                try:
                    self.esConnection = esConnect()
                    return
                except (ElasticsearchBadServer, ElasticsearchInvalidIndex, ElasticsearchException) as e:
                    logger.exception("ElasticSearchException: {0} reported while indexing event".format(e))
                    return
            except ElasticsearchException as e:
                logger.exception("ElasticSearchException: {0} reported while indexing event".format(e))
                logger.error("Malformed jbody: %r" % jbody)
                return
        except Exception as e:
            logger.exception(e)
            logger.error("Malformed message: %r" % event)


def esConnect():
    """open or re-open a connection to elastic search"""
    return ElasticsearchClient((list("{0}".format(s) for s in options.esservers)), options.esbulksize)


def initConfig():
    # capture the hostname
    options.mozdefhostname = getConfig("mozdefhostname", socket.gethostname(), options.configfile)

    # elastic search options. set esbulksize to a non-zero value to enable bulk posting, set timeout to post no matter how many events after X seconds.
    options.esservers = list(getConfig("esservers", "http://localhost:9200", options.configfile).split(","))
    options.esbulksize = getConfig("esbulksize", 0, options.configfile)
    options.esbulktimeout = getConfig("esbulktimeout", 30, options.configfile)

    # GCP PubSub options
    options.resource_name = getConfig("resource_name", "", options.configfile)
    options.credentials_file = getConfig("credentials_file", "", options.configfile)

    options.mqprotocol = getConfig("mqprotocol", "pubsub", options.configfile)


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
        "-c", dest="configfile", default=sys.argv[0].replace(".py", ".conf"), help="configuration file to use"
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
