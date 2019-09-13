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
    def nothing():
        return

    def onMessage(self, message):
        print(message)
        taskConsumer.onMessage(message)


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
