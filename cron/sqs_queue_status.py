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
import os
import sys
from configlib import getConfig, OptionParser
from datetime import datetime
from hashlib import md5
import boto3

from mozdef_util.utilities.toUTC import toUTC
from mozdef_util.utilities.logger import logger
from mozdef_util.elasticsearch_client import ElasticsearchClient


def getDocID(sqsregionidentifier):
    # create a hash to use as the ES doc id
    # hostname plus salt as doctype.latest
    hash = md5()
    seed = '{0}.mozdefhealth.latest'.format(sqsregionidentifier)
    hash.update(seed.encode())
    return hash.hexdigest()


def getQueueSizes():
    logger.debug('starting')
    logger.debug(options)
    es = ElasticsearchClient(options.esservers)

    sqs_client = boto3.client(
        "sqs",
        region_name=options.region,
        aws_access_key_id=options.accesskey,
        aws_secret_access_key=options.secretkey
    )
    queues_stats = {
        'queues': [],
        'total_feeds': len(options.taskexchange),
        'total_messages_ready': 0,
        'username': 'mozdef'
    }
    for queue_name in options.taskexchange:
        logger.debug('Looking for sqs queue stats in queue' + queue_name)
        queue_url = sqs_client.get_queue_url(QueueName=queue_name)['QueueUrl']
        queue_attributes = sqs_client.get_queue_attributes(QueueUrl=queue_url, AttributeNames=['All'])['Attributes']
        queue_stats = {
            'queue': queue_name,
        }
        if 'ApproximateNumberOfMessages' in queue_attributes:
            queue_stats['messages_ready'] = int(queue_attributes['ApproximateNumberOfMessages'])
            queues_stats['total_messages_ready'] += queue_stats['messages_ready']
        if 'ApproximateNumberOfMessagesNotVisible' in queue_attributes:
            queue_stats['messages_inflight'] = int(queue_attributes['ApproximateNumberOfMessagesNotVisible'])
        if 'ApproximateNumberOfMessagesDelayed' in queue_attributes:
            queue_stats['messages_delayed'] = int(queue_attributes['ApproximateNumberOfMessagesDelayed'])

        queues_stats['queues'].append(queue_stats)

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
        details=queues_stats)
    healthlog['tags'] = ['mozdef', 'status', 'sqs']
    healthlog['type'] = 'mozdefhealth'
    # post to elasticsearch servers directly without going through
    # message queues in case there is an availability issue
    es.save_event(index=options.index, body=json.dumps(healthlog))
    # post another doc with a static docid and tag
    # for use when querying for the latest sqs status
    healthlog['tags'] = ['mozdef', 'status', 'sqs-latest']
    es.save_event(index=options.index, doc_id=getDocID(sqsid), body=json.dumps(healthlog))


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
