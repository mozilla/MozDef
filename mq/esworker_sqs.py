#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# Copyright (c) 2014 Mozilla Corporation

# kombu's support for SQS is buggy
# so this version uses boto
# to read an SQS queue and put events into elastic search
# in the same manner as esworker_eventtask.py


import json
import sys
import socket
import time
from configlib import getConfig, OptionParser
from datetime import datetime
import base64
from ssl import SSLEOFError, SSLError

from mozdef_util.utilities.toUTC import toUTC
from mozdef_util.utilities.to_unicode import toUnicode
from mozdef_util.utilities.remove_at import removeAt
from mozdef_util.utilities.logger import logger, initLogger
from mozdef_util.elasticsearch_client import (
    ElasticsearchClient,
    ElasticsearchBadServer,
    ElasticsearchInvalidIndex,
    ElasticsearchException,
)

from lib.plugins import sendEventToPlugins, registerPlugins
from lib.sqs import connect_sqs


# running under uwsgi?
try:
    import uwsgi

    hasUWSGI = True
except ImportError as e:
    hasUWSGI = False


def keyMapping(aDict):
    """map common key/fields to a normalized structure,
       explicitly typed when possible to avoid schema changes for upsteam consumers
       Special accomodations made for logstash,nxlog, beaver, heka and CEF
       Some shippers attempt to conform to logstash-style @fieldname convention.
       This strips the leading at symbol since it breaks some elastic search
       libraries like elasticutils.
    """
    returndict = dict()

    # uncomment to save the source event for debugging, or chain of custody/forensics
    # returndict['original']=aDict

    # set the timestamp when we received it, i.e. now
    returndict["receivedtimestamp"] = toUTC(datetime.now()).isoformat()
    returndict["mozdefhostname"] = options.mozdefhostname
    returndict["details"] = {}
    try:
        for k, v in aDict.items():
            k = removeAt(k).lower()

            if k in ("message", "summary"):
                returndict["summary"] = toUnicode(v)

            if k in ("payload") and "summary" not in aDict:
                # special case for heka if it sends payload as well as a summary, keep both but move payload to the details section.
                returndict["summary"] = toUnicode(v)
            elif k in ("payload"):
                returndict["details"]["payload"] = toUnicode(v)

            if k in ("eventtime", "timestamp", "utctimestamp"):
                returndict["utctimestamp"] = toUTC(v).isoformat()
                returndict["timestamp"] = toUTC(v).isoformat()

            if k in ("hostname", "source_host", "host"):
                returndict["hostname"] = toUnicode(v)

            if k in ("tags"):
                if len(v) > 0:
                    returndict["tags"] = v

            # nxlog keeps the severity name in syslogseverity,everyone else should use severity or level.
            if k in ("syslogseverity", "severity", "severityvalue", "level"):
                returndict["severity"] = toUnicode(v).upper()

            if k in ("facility", "syslogfacility", "source"):
                returndict["source"] = toUnicode(v)

            if k in ("pid", "processid"):
                returndict["processid"] = toUnicode(v)

            # nxlog sets sourcename to the processname (i.e. sshd), everyone else should call it process name or pname
            if k in ("pname", "processname", "sourcename"):
                returndict["processname"] = toUnicode(v)

            # the file, or source
            if k in ("path", "logger", "file"):
                returndict["eventsource"] = toUnicode(v)

            if k in ("type", "eventtype", "category"):
                returndict["category"] = toUnicode(v)

            # custom fields as a list/array
            if k in ("fields", "details"):
                if type(v) is not dict:
                    returndict["details"]["message"] = v
                else:
                    if len(v) > 0:
                        for details_key, details_value in v.items():
                            returndict["details"][details_key] = details_value

            # custom fields/details as a one off, not in an array
            # i.e. fields.something=value or details.something=value
            # move them to a dict for consistency in querying
            if k.startswith("fields.") or k.startswith("details."):
                newName = k.replace("fields.", "")
                newName = newName.lower().replace("details.", "")
                # add field with a special case for shippers that
                # don't send details
                # in an array as int/floats/strings
                # we let them dictate the data type with field_datatype
                # convention
                if newName.endswith("_int"):
                    returndict["details"][str(newName)] = int(v)
                elif newName.endswith("_float"):
                    returndict["details"][str(newName)] = float(v)
                else:
                    returndict["details"][str(newName)] = toUnicode(v)

        # nxlog windows log handling
        if "Domain" in aDict and "SourceModuleType" in aDict:
            # nxlog parses all windows event fields very well
            # copy all fields to details
            returndict["details"][k] = v

        if "utctimestamp" not in returndict:
            # default in case we don't find a reasonable timestamp
            returndict["utctimestamp"] = toUTC(datetime.now()).isoformat()

        if "type" not in returndict:
            # default replacement for old _type subcategory.
            # to preserve filtering capabilities
            returndict["type"] = "event"

    except Exception as e:
        logger.exception("Exception normalizing the message %r" % e)
        logger.error("Malformed message dict: %r" % aDict)
        return None

    return returndict


def esConnect():
    """open or re-open a connection to elastic search"""
    return ElasticsearchClient((list("{0}".format(s) for s in options.esservers)), options.esbulksize)


class taskConsumer(object):
    def __init__(self, queue, esConnection):
        self.sqs_queue = queue
        self.esConnection = esConnection

    def run(self):
        while True:
            try:
                records = self.sqs_queue.receive_messages(MaxNumberOfMessages=options.prefetch)
                for msg in records:
                    # msg.id is the id,
                    # get_body() should be json

                    # pre process the message a bit
                    tmp = msg.body
                    try:
                        msgbody = json.loads(tmp)
                    except ValueError:
                        # If Boto wrote to the queue, it might be base64 encoded, so let's decode that
                        try:
                            tmp = base64.b64decode(tmp)
                            msgbody = json.loads(tmp)
                        except Exception as e:
                            logger.error(
                                "Invalid message, not JSON <dropping message and continuing>: %r" % msg.get_body()
                            )
                            msg.delete()
                            continue

                    # If this is still not a dict,
                    # let's just drop the message and move on
                    if type(msgbody) is not dict:
                        logger.debug("Message is not a dictionary, dropping message.")
                        msg.delete()
                        continue

                    event = dict()
                    event = msgbody

                    if "tags" in event:
                        event["tags"].extend([options.taskexchange])
                    else:
                        event["tags"] = [options.taskexchange]

                    # process message
                    self.on_message(event, msg)

                    # delete message from queue
                    msg.delete()
                time.sleep(options.sleep_time)

            except ValueError as e:
                logger.exception("Exception while handling message: %r" % e)
                msg.delete()
            except (SSLEOFError, SSLError, socket.error):
                logger.info("Received network related error...reconnecting")
                time.sleep(5)
                self.sqs_queue = connect_sqs(options.region, options.accesskey, options.secretkey, options.taskexchange)

    def on_message(self, body, message):
        # print("RECEIVED MESSAGE: %r" % (body, ))
        try:
            # default elastic search metadata for an event
            metadata = {"index": "events", "id": None}
            # just to be safe..check what we were sent.
            if isinstance(body, dict):
                bodyDict = body
            elif isinstance(body, str):
                try:
                    bodyDict = json.loads(body)  # lets assume it's json
                except ValueError as e:
                    # not json..ack but log the message
                    logger.error("Exception: unknown body type received %r" % body)
                    # message.ack()
                    return
            else:
                logger.error("Exception: unknown body type received %r" % body)
                # message.ack()
                return

            if "customendpoint" in bodyDict and bodyDict["customendpoint"]:
                # custom document
                # send to plugins to allow them to modify it if needed
                (normalizedDict, metadata) = sendEventToPlugins(bodyDict, metadata, pluginList)
            else:
                # normalize the dict
                # to the mozdef events standard
                normalizedDict = keyMapping(bodyDict)

                # send to plugins to allow them to modify it if needed
                if normalizedDict is not None and isinstance(normalizedDict, dict):
                    (normalizedDict, metadata) = sendEventToPlugins(normalizedDict, metadata, pluginList)

            # drop the message if a plug in set it to None
            # signaling a discard
            if normalizedDict is None:
                # message.ack()
                return

            # make a json version for posting to elastic search
            jbody = json.JSONEncoder().encode(normalizedDict)

            try:
                bulk = False
                if options.esbulksize != 0:
                    bulk = True

                self.esConnection.save_event(index=metadata["index"], doc_id=metadata["id"], body=jbody, bulk=bulk)

            except (ElasticsearchBadServer, ElasticsearchInvalidIndex) as e:
                # handle loss of server or race condition with index rotation/creation/aliasing
                try:
                    self.esConnection = esConnect()
                    # message.requeue()
                    return
                except (ElasticsearchBadServer, ElasticsearchInvalidIndex, ElasticsearchException):
                    # there's no requeue and we drop several messages
                    # state may be already set.
                    logger.exception(
                        "ElasticSearchException: {0} reported while indexing event, messages lost".format(e)
                    )
                    return
            except ElasticsearchException as e:
                # exception target for queue capacity issues reported by elastic search so catch the error, report it and retry the message
                logger.exception("ElasticSearchException: {0} reported while indexing event, messages lost".format(e))
                # there's no requeue and we drop several messages
                # message.requeue()
                return

        except Exception as e:
            logger.exception(e)
            logger.error("Malformed message body: %r" % body)


def main():
    # meant only to talk to SQS using boto
    # and process events as json.

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
    taskConsumer(sqs_queue, es).run()


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
    options.mqserver = getConfig("mqserver", "localhost", options.configfile)
    options.taskexchange = getConfig("taskexchange", "eventtask", options.configfile)
    # rabbit: how many messages to ask for at once from the message queue
    options.prefetch = getConfig("prefetch", 10, options.configfile)
    # rabbit: user creds
    options.mquser = getConfig("mquser", "guest", options.configfile)
    options.mqpassword = getConfig("mqpassword", "guest", options.configfile)
    # rabbit: port/vhost
    options.mqport = getConfig("mqport", 5672, options.configfile)
    options.mqvhost = getConfig("mqvhost", "/", options.configfile)

    # rabbit: run with message acking?
    # also toggles transient/persistant delivery (messages in memory only or stored on disk)
    # ack=True sets persistant delivery, False sets transient delivery
    options.mqack = getConfig("mqack", True, options.configfile)

    # aws options
    options.accesskey = getConfig("accesskey", "", options.configfile)
    options.secretkey = getConfig("secretkey", "", options.configfile)
    options.region = getConfig("region", "", options.configfile)

    # How long to sleep between polling
    options.sleep_time = getConfig("sleep_time", 0.1, options.configfile)


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

    pluginList = registerPlugins()

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
