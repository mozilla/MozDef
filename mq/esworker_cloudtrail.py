#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# Copyright (c) 2017 Mozilla Corporation


import json
import os
import sys
import socket
from configlib import getConfig, OptionParser
from datetime import datetime
import boto3
import gzip
from io import BytesIO
import re
import time
from ssl import SSLEOFError, SSLError
from threading import Thread

from mozdef_util.utilities.toUTC import toUTC
from mozdef_util.elasticsearch_client import (
    ElasticsearchClient,
    ElasticsearchBadServer,
    ElasticsearchInvalidIndex,
    ElasticsearchException,
)
from mozdef_util.utilities.logger import logger, initLogger
from mozdef_util.utilities.to_unicode import toUnicode
from mozdef_util.utilities.remove_at import removeAt

from lib.aws import get_aws_credentials
from lib.plugins import sendEventToPlugins, registerPlugins
from lib.sqs import connect_sqs


CLOUDTRAIL_VERB_REGEX = re.compile(r"^([A-Z][^A-Z]*)")

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

    returndict["source"] = "cloudtrail"
    returndict["details"] = {}
    returndict["category"] = "cloudtrail"
    returndict["processid"] = str(os.getpid())
    returndict["processname"] = sys.argv[0]
    returndict["tags"] = [options.taskexchange]
    returndict["severity"] = "INFO"
    if "sourceIPAddress" in aDict and "eventName" in aDict and "eventSource" in aDict:
        summary_str = "{0} performed {1} in {2}".format(
            aDict["sourceIPAddress"], aDict["eventName"], aDict["eventSource"]
        )
        returndict["summary"] = summary_str

    if "eventName" in aDict:
        # Uppercase first character
        aDict["eventName"] = aDict["eventName"][0].upper() + aDict["eventName"][1:]
        returndict["details"]["eventVerb"] = CLOUDTRAIL_VERB_REGEX.findall(aDict["eventName"])[0]
        returndict["details"]["eventReadOnly"] = returndict["details"]["eventVerb"] in ["Describe", "Get", "List"]
    # set the timestamp when we received it, i.e. now
    returndict["receivedtimestamp"] = toUTC(datetime.now()).isoformat()
    returndict["mozdefhostname"] = options.mozdefhostname
    try:
        for k, v in aDict.items():
            k = removeAt(k).lower()

            if k == "sourceip":
                returndict["details"]["sourceipaddress"] = v

            elif k == "sourceipaddress":
                returndict["details"]["sourceipaddress"] = v

            elif k in ("facility", "source"):
                returndict["source"] = v

            elif k in ("eventsource"):
                returndict["hostname"] = v

            elif k in ("message", "summary"):
                returndict["summary"] = toUnicode(v)

            elif k in ("payload") and "summary" not in aDict:
                # special case for heka if it sends payload as well as a summary, keep both but move payload to the details section.
                returndict["summary"] = toUnicode(v)
            elif k in ("payload"):
                returndict["details"]["payload"] = toUnicode(v)

            elif k in ("eventtime", "timestamp", "utctimestamp", "date"):
                returndict["utctimestamp"] = toUTC(v).isoformat()
                returndict["timestamp"] = toUTC(v).isoformat()

            elif k in ("hostname", "source_host", "host"):
                returndict["hostname"] = toUnicode(v)

            elif k in ("tags"):
                if "tags" not in returndict:
                    returndict["tags"] = []
                if type(v) == list:
                    returndict["tags"] += v
                else:
                    if len(v) > 0:
                        returndict["tags"].append(v)

            # nxlog keeps the severity name in syslogseverity,everyone else should use severity or level.
            elif k in ("syslogseverity", "severity", "severityvalue", "level", "priority"):
                returndict["severity"] = toUnicode(v).upper()

            elif k in ("facility", "syslogfacility"):
                returndict["facility"] = toUnicode(v)

            elif k in ("pid", "processid"):
                returndict["processid"] = toUnicode(v)

            # nxlog sets sourcename to the processname (i.e. sshd), everyone else should call it process name or pname
            elif k in ("pname", "processname", "sourcename", "program"):
                returndict["processname"] = toUnicode(v)

            # the file, or source
            elif k in ("path", "logger", "file"):
                returndict["eventsource"] = toUnicode(v)

            elif k in ("type", "eventtype", "category"):
                returndict["category"] = toUnicode(v)
                returndict["type"] = "cloudtrail"

            # custom fields as a list/array
            elif k in ("fields", "details"):
                if type(v) is not dict:
                    returndict["details"]["message"] = v
                else:
                    if len(v) > 0:
                        for details_key, details_value in v.items():
                            returndict["details"][details_key] = details_value

            # custom fields/details as a one off, not in an array
            # i.e. fields.something=value or details.something=value
            # move them to a dict for consistency in querying
            elif k.startswith("fields.") or k.startswith("details."):
                newName = k.replace("fields.", "")
                newName = newName.lower().replace("details.", "")
                # add a dict to hold the details if it doesn't exist
                if "details" not in returndict:
                    returndict["details"] = dict()
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
            else:
                returndict["details"][k] = v

        if "utctimestamp" not in returndict:
            # default in case we don't find a reasonable timestamp
            returndict["utctimestamp"] = toUTC(datetime.now()).isoformat()

    except Exception as e:
        logger.exception(e)
        logger.error("Malformed message: %r" % aDict)

    return returndict


def esConnect():
    """open or re-open a connection to elastic search"""
    return ElasticsearchClient(
        (list("{0}".format(s) for s in options.esservers)),
        bulk_amount=options.esbulksize,
        bulk_refresh_time=options.esbulktimeout,
    )


class taskConsumer(object):
    def __init__(self, queue, esConnection):
        self.sqs_queue = queue
        self.esConnection = esConnection
        self.s3_client = None
        self.authenticate()

        # Run thread to flush s3 credentials
        reauthenticate_thread = Thread(target=self.reauth_timer)
        reauthenticate_thread.daemon = True
        reauthenticate_thread.start()

    def authenticate(self):
        # This value controls how long we sleep
        # between reauthenticating and getting a new set of creds
        # eventually this gets set by aws response
        self.flush_wait_time = 1800
        if options.cloudtrail_arn not in ["<cloudtrail_arn>", "cloudtrail_arn"]:
            client = boto3.client("sts", aws_access_key_id=options.accesskey, aws_secret_access_key=options.secretkey)
            response = client.assume_role(RoleArn=options.cloudtrail_arn, RoleSessionName="MozDef-CloudTrail-Reader")
            role_creds = {
                "aws_access_key_id": response["Credentials"]["AccessKeyId"],
                "aws_secret_access_key": response["Credentials"]["SecretAccessKey"],
                "aws_session_token": response["Credentials"]["SessionToken"],
            }
            current_time = toUTC(datetime.now())
            # Let's remove 3 seconds from the flush wait time just in case
            self.flush_wait_time = (response["Credentials"]["Expiration"] - current_time).seconds - 3
        else:
            role_creds = {}
        role_creds["region_name"] = options.region
        self.s3_client = boto3.client("s3", **get_aws_credentials(**role_creds))

    def reauth_timer(self):
        while True:
            time.sleep(self.flush_wait_time)
            logger.debug("Recycling credentials and reassuming role")
            self.authenticate()

    def parse_s3_file(self, s3_obj):
        compressed_data = s3_obj["Body"].read()
        databuf = BytesIO(compressed_data)
        gzip_file = gzip.GzipFile(fileobj=databuf)
        json_logs = json.loads(gzip_file.read())
        return json_logs["Records"]

    def run(self):
        while True:
            try:
                records = self.sqs_queue.receive_messages(MaxNumberOfMessages=options.prefetch)
                for msg in records:
                    body_message = msg.body
                    event = json.loads(body_message)

                    if not event["Message"]:
                        logger.error("Invalid message format for cloudtrail SQS messages")
                        logger.error("Malformed Message: %r" % body_message)
                        continue

                    if event["Message"] == "CloudTrail validation message.":
                        # We don't care about these messages
                        continue

                    message_json = json.loads(event["Message"])

                    if "s3ObjectKey" not in message_json:
                        logger.error("Invalid message format, expecting an s3ObjectKey in Message")
                        logger.error("Malformed Message: %r" % body_message)
                        continue

                    s3_log_files = message_json["s3ObjectKey"]
                    for log_file in s3_log_files:
                        logger.debug("Downloading and parsing " + log_file)
                        s3_obj = self.s3_client.get_object(Bucket=message_json["s3Bucket"], Key=log_file)
                        events = self.parse_s3_file(s3_obj)
                        for event in events:
                            self.on_message(event)

                    msg.delete()
            except (SSLEOFError, SSLError, socket.error):
                logger.info("Received network related error...reconnecting")
                time.sleep(5)
                self.sqs_queue = connect_sqs(
                    region_name=options.region,
                    aws_access_key_id=options.accesskey,
                    aws_secret_access_key=options.secretkey,
                    task_exchange=options.taskexchange,
                )
            time.sleep(options.sleep_time)

    def on_message(self, body):
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
                    logger.error("Unknown body type received %r" % body)
                    return
            else:
                logger.error("Unknown body type received %r\n" % body)
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
                return

            # make a json version for posting to elastic search
            jbody = json.JSONEncoder().encode(normalizedDict)

            try:
                bulk = False
                if options.esbulksize != 0:
                    bulk = True

                bulk = False
                self.esConnection.save_event(index=metadata["index"], doc_id=metadata["id"], body=jbody, bulk=bulk)

            except (ElasticsearchBadServer, ElasticsearchInvalidIndex) as e:
                # handle loss of server or race condition with index rotation/creation/aliasing
                try:
                    self.esConnection = esConnect()
                    return
                except (ElasticsearchBadServer, ElasticsearchInvalidIndex, ElasticsearchException):
                    logger.exception(
                        "ElasticSearchException: {0} reported while indexing event, messages lost".format(e)
                    )
                    return
            except ElasticsearchException as e:
                # exception target for queue capacity issues reported by elastic search so catch the error, report it and retry the message
                logger.exception("ElasticSearchException: {0} reported while indexing event, messages lost".format(e))
                return
        except Exception as e:
            logger.exception(e)
            logger.error("Malformed message: %r" % body)


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

    # output our log to stdout or syslog
    options.output = getConfig("output", "stdout", options.configfile)
    options.sysloghostname = getConfig("sysloghostname", "localhost", options.configfile)
    options.syslogport = getConfig("syslogport", 514, options.configfile)

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

    # aws options
    options.accesskey = getConfig("accesskey", "", options.configfile)
    options.secretkey = getConfig("secretkey", "", options.configfile)
    options.region = getConfig("region", "", options.configfile)

    # This is the full ARN that the s3 bucket lives under
    options.cloudtrail_arn = getConfig("cloudtrail_arn", "cloudtrail_arn", options.configfile)

    # How long to sleep between iterations of querying AWS
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
