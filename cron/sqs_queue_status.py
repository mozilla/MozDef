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
from configlib import getConfig, OptionParser
from datetime import datetime
from hashlib import md5
import boto.sqs

from mozdef_util.utilities.toUTC import toUTC
from mozdef_util.utilities.logger import logger, initLogger
from mozdef_util.elasticsearch_client import ElasticsearchClient


def getDocID(sqsregionidentifier):
    # create a hash to use as the ES doc id
    # hostname plus salt as doctype.latest
    hash = md5()
    hash.update('{0}.mozdefhealth.latest'.format(sqsregionidentifier))
    return hash.hexdigest()


def getQueueSizes():
    logger.debug('starting')
    logger.debug(options)
    es = ElasticsearchClient(options.esservers)
    sqslist = {}
    sqslist['queue_stats'] = {}
    qcount = len(options.taskexchange)
    qcounter = qcount - 1

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

    # setup a log entry for health/status.
    sqsid = '{0}-{1}'.format(options.account, options.region)
    healthlog = dict(
        utctimestamp=toUTC(datetime.now()).isoformat(),
        hostname=sqsid,
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
        healthlog['details']['queues'].append(queueinfo)
        qcounter -= 1
    # post to elasticsearch servers directly without going through
    # message queues in case there is an availability issue
    es.save_event(index=options.index, doc_type='_doc', body=json.dumps(healthlog))
    # post another doc with a static docid and tag
    # for use when querying for the latest sqs status
    healthlog['tags'] = ['mozdef', 'status', 'sqs-latest']
    es.save_event(index=options.index, doc_type='_doc', doc_id=getDocID(sqsid), body=json.dumps(healthlog))
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
    main()
