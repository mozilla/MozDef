#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
# Copyright (c) 2017 Mozilla Corporation


import json

import sys
import os
import socket
import time
from configlib import getConfig, OptionParser
from datetime import datetime
import pytz

from mozdef_util.utilities.toUTC import toUTC
from mozdef_util.utilities.logger import logger, initLogger
from mozdef_util.elasticsearch_client import (
    ElasticsearchClient,
    ElasticsearchBadServer,
    ElasticsearchInvalidIndex,
    ElasticsearchException,
)

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../"))
from mq.lib.plugins import sendEventToPlugins, registerPlugins
from mq.lib.sqs import connect_sqs
from esworker_sns_sqs import taskConsumer


# running under uwsgi?
try:
    import uwsgi

    hasUWSGI = True
except ImportError as e:
    hasUWSGI = False


class GDtaskConsumer(taskConsumer):
    def build_submit_message(self, message):
        # default elastic search metadata for an event
        metadata = {"index": "events", "id": None}

        event = {}

        event["receivedtimestamp"] = toUTC(datetime.now()).isoformat()
        event["mozdefhostname"] = self.options.mozdefhostname

        if "tags" in event:
            event["tags"].extend([self.options.taskexchange])
        else:
            event["tags"] = [self.options.taskexchange]

        event["severity"] = "INFO"
        event["source"] = "guardduty"
        event["details"] = {}

        event["details"] = message["details"]
        if "hostname" in message:
            event["hostname"] = message["hostname"]
        if "summary" in message:
            event["summary"] = message["summary"]
        if "category" in message:
            event["details"]["category"] = message["category"]
        if "tags" in message:
            event["details"]["tags"] = message["tags"]
        event["utctimestamp"] = toUTC(message["timestamp"]).isoformat()
        event["timestamp"] = event["utctimestamp"]
        (event, metadata) = sendEventToPlugins(event, metadata, self.pluginList)
        # Drop message if plugins set to None
        if event is None:
            return

        self.save_event(event, metadata)

    def on_message(self, message_raw):
        if "Message" in message_raw:
            event = {}
            message = json.loads(message_raw["Message"])
            if "details" in message:
                if "finding" in message["details"]:
                    if "action" in message["details"]["finding"]:
                        if "actionType" in message["details"]["finding"]["action"]:
                            if message["details"]["finding"]["action"]["actionType"] == "PORT_PROBE":
                                if "portProbeAction" in message["details"]["finding"]["action"]:
                                    if "portProbeDetails" in message["details"]["finding"]["action"]["portProbeAction"]:
                                        for probe in message["details"]["finding"]["action"]["portProbeAction"][
                                            "portProbeDetails"
                                        ]:
                                            isolatedmessage = message
                                            del isolatedmessage["details"]["finding"]["action"]["portProbeAction"][
                                                "portProbeDetails"
                                            ]
                                            isolatedmessage["details"]["finding"]["action"]["portProbeAction"][
                                                "portProbeDetails"
                                            ] = probe
                                            self.build_submit_message(message)
                            else:
                                self.build_submit_message(message)


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

    # set to sqs for Amazon
    options.mqprotocol = getConfig("mqprotocol", "sqs", options.configfile)

    # rabbit message queue options
    options.taskexchange = getConfig("taskexchange", "eventtask", options.configfile)
    # rabbit: how many messages to ask for at once from the message queue
    options.prefetch = getConfig("prefetch", 10, options.configfile)

    # aws options
    options.accesskey = getConfig("accesskey", "", options.configfile)
    options.secretkey = getConfig("secretkey", "", options.configfile)
    options.region = getConfig("region", "", options.configfile)

    # How long to sleep between polling
    options.sleep_time = getConfig("sleep_time", 0.1, options.configfile)


def main():
    if hasUWSGI:
        logger.info("started as uwsgi mule {0}".format(uwsgi.mule_id()))
    else:
        logger.info("started without uwsgi")

    if options.mqprotocol not in ("sqs"):
        logger.error("Can only process SQS queues, terminating")
        sys.exit(1)

    sqs_queue = connect_sqs(
        region_name=options.region,
        aws_access_key_id=options.accesskey,
        aws_secret_access_key=options.secretkey,
        task_exchange=options.taskexchange,
    )
    # consume our queue
    GDtaskConsumer(sqs_queue, es, options).run()


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
