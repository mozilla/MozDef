#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
# Copyright (c) 2014 Mozilla Corporation

# kombu's support for SQS is buggy
# so this version uses boto
# to read an SQS queue and put events into elastic search
# in the same manner as esworker_eventtask.py


import json
import os
import sys
import socket
import time
from configlib import getConfig, OptionParser
from datetime import datetime
from hashlib import md5
import boto.sqs
from boto.sqs.message import RawMessage
import base64
import kombu

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../lib'))
from utilities.toUTC import toUTC
from utilities.to_unicode import toUnicode
from utilities.remove_at import removeAt
from utilities.is_cef import isCEF
from utilities.logger import logger, initLogger
from elasticsearch_client import ElasticsearchClient, ElasticsearchBadServer, ElasticsearchInvalidIndex, ElasticsearchException

def getDocID(account):
    # create a hash to use as the ES doc id
    # hostname plus salt as doctype.latest
    hash = md5()
    hash.update('{0}.mozdefhealth.latest'.format(account))
    return hash.hexdigest()

def getQueueSizes():
    logger.debug('starting')
    logger.debug(options)
    es = ElasticsearchClient(options.esservers)
    sqslist = {}
    sqslist['queue_stats'] = {}
    qcount = len(options.taskexchange)
    qcounter = qcount - 1
    try:
        # meant only to talk to SQS using boto
        # and return queue attributes.a

        mqConn = boto.sqs.connect_to_region(
            options.region,
            aws_access_key_id=options.accesskey,
            aws_secret_access_key=options.secretkey
        )

        while qcounter >= 0:
            for exchange in options.taskexchange:
                logger.debug('Looking for sqs queue stats in queue' + exchange)
                eventTaskQueue = mqConn.get_queue(exchange)
                # get queue stats
                taskQueueStats = eventTaskQueue.get_attributes('All')
                sqslist['queue_stats'][qcounter] = taskQueueStats
                sqslist['queue_stats'][qcounter]['name'] = exchange
                qcounter -= 1
    except Exception as e:
        logger.error("Exception %r when gathering health and status " % e)


    # setup a log entry for health/status.
    healthlog = dict(
        utctimestamp=toUTC(datetime.now()).isoformat(),
        hostname='server',
        processid=os.getpid(),
        processname=sys.argv[0],
        severity='INFO',
        summary='mozdef health/status',
        category='mozdef',
        source='aws-sqs',
        tags=[],
        details=[])
    healthlog['details'] = dict(username='mozdef')
    healthlog['details']['queues']= list()
    healthlog['details']['total_messages_ready'] = 0
    healthlog['details']['total_feeds'] = qcount
    healthlog['tags'] = ['mozdef', 'status', 'sqs']
    ready = 0
    qcounter = qcount - 1
    for q in sqslist['queue_stats'].keys():
        queuelist = sqslist['queue_stats'][qcounter]
        if 'ApproximateNumberOfMessages' in queuelist:
            ready1 = int(queuelist['ApproximateNumberOfMessages'])
            ready = ready1 + ready
            healthlog['details']['total_messages_ready'] = ready
        if 'ApproximateNumberOfMessages' in queuelist:
            messages = int(queuelist['ApproximateNumberOfMessages'])
        if 'ApproximateNumberOfMessagesNotVisible' in queuelist:
            inflight = int(queuelist['ApproximateNumberOfMessagesNotVisible'])
        if 'ApproximateNumberOfMessagesDelayed' in queuelist:
            delayed = int(queuelist['ApproximateNumberOfMessagesDelayed'])
        if 'name' in queuelist:
            name = queuelist['name']
        queueinfo=dict(
            queue=name,
            messages_delayed=delayed,
            messages_ready=messages,
            messages_inflight=inflight)
        print queueinfo
        healthlog['details']['queues'].append(queueinfo)
        qcounter -= 1
    es.save_event(index=options.index, doc_type='mozdefhealth', body=json.dumps(healthlog))
#    except Exception as e:
#        logger.error("Exception %r when gathering health and status " % e)

def main():
    logger.debug('Starting')
    logger.debug(options)
    getQueueSizes()

def initConfig():
    # aws options
    options.accesskey = getConfig('accesskey', '', options.configfile)
    options.secretkey = getConfig('secretkey', '', options.configfile)
    options.region = getConfig('region', 'us-west-1', options.configfile)
    options.taskexchange = getConfig('taskexchange', 'nsmglobalssqslists', options.configfile).split(',')
    options.output = getConfig('output', 'stdout', options.configfile)
    # mozdef options
    options.sysloghostname = getConfig('sysloghostname', 'localhost', options.configfile)
    options.syslogport = getConfig('syslogport', 514, options.configfile)
    options.esservers = list(getConfig('esservers', 'http://localhost:9200', options.configfile).split(','))
    options.index = getConfig('index', 'mozdefstate', options.configfile)
    options.account = getConfig('account', '', options.configfile)

if __name__ == '__main__':
    # configure ourselves
    parser = OptionParser()
    parser.add_option("-c", dest='configfile', default=sys.argv[0].replace('.py', '.conf'), help="configuration file to use")
    (options, args) = parser.parse_args()
    initConfig()
    initLogger(options)
    main()
