#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# Copyright (c) 2014 Mozilla Corporation

import json
import os
import requests
import sys
from datetime import datetime
from hashlib import md5
from requests.auth import HTTPBasicAuth
from configlib import getConfig, OptionParser

from mozdef_util.utilities.logger import logger
from mozdef_util.utilities.toUTC import toUTC
from mozdef_util.elasticsearch_client import ElasticsearchClient


def getDocID(servername):
    # create a hash to use as the ES doc id
    # hostname plus salt as doctype.latest
    hash = md5()
    seed = '{0}.mozdefhealth.latest'.format(servername)
    hash.update(seed.encode())
    return hash.hexdigest()


def main():
    '''
    Get health and status stats and post to ES
    Post both as a historical reference (for charts)
    and as a static docid (for realtime current health/EPS displays)
    '''
    logger.debug('starting')
    logger.debug(options)
    es = ElasticsearchClient((list('{0}'.format(s) for s in options.esservers)))
    index = options.index

    with open(options.default_mapping_file, 'r') as mapping_file:
        default_mapping_contents = json.loads(mapping_file.read())

    if not es.index_exists(index):
        try:
            logger.debug('Creating %s index' % index)
            es.create_index(index, default_mapping_contents)
        except Exception as e:
            logger.error("Unhandled exception, terminating: %r" % e)

    auth = HTTPBasicAuth(options.mquser, options.mqpassword)

    for server in options.mqservers:
        logger.debug('checking message queues on {0}'.format(server))
        r = requests.get(
            'http://{0}:{1}/api/queues'.format(server,
                                               options.mqapiport),
            auth=auth)

        mq = r.json()
        # setup a log entry for health/status.
        healthlog = dict(
            utctimestamp=toUTC(datetime.now()).isoformat(),
            hostname=server,
            processid=os.getpid(),
            processname=sys.argv[0],
            severity='INFO',
            summary='mozdef health/status',
            category='mozdef',
            type='mozdefhealth',
            source='mozdef',
            tags=[],
            details=[])

        healthlog['details'] = dict(username='mozdef')
        healthlog['details']['loadaverage'] = list(os.getloadavg())
        healthlog['details']['queues']=list()
        healthlog['details']['total_deliver_eps'] = 0
        healthlog['details']['total_publish_eps'] = 0
        healthlog['details']['total_messages_ready'] = 0
        healthlog['tags'] = ['mozdef', 'status']
        for m in mq:
            if 'message_stats' in m and isinstance(m['message_stats'], dict):
                if 'messages_ready' in m:
                    mready = m['messages_ready']
                    healthlog['details']['total_messages_ready'] += m['messages_ready']
                else:
                    mready = 0
                if 'messages_unacknowledged' in m:
                    munack = m['messages_unacknowledged']
                else:
                    munack = 0
                queueinfo=dict(
                    queue=m['name'],
                    vhost=m['vhost'],
                    messages_ready=mready,
                    messages_unacknowledged=munack)

                if 'deliver_details' in m['message_stats']:
                    queueinfo['deliver_eps'] = round(m['message_stats']['deliver_details']['rate'], 2)
                    healthlog['details']['total_deliver_eps'] += round(m['message_stats']['deliver_details']['rate'], 2)
                if 'deliver_no_ack_details' in m['message_stats']:
                    queueinfo['deliver_eps'] = round(m['message_stats']['deliver_no_ack_details']['rate'], 2)
                    healthlog['details']['total_deliver_eps'] += round(m['message_stats']['deliver_no_ack_details']['rate'], 2)
                if 'publish_details' in m['message_stats']:
                    queueinfo['publish_eps'] = round(m['message_stats']['publish_details']['rate'], 2)
                    healthlog['details']['total_publish_eps'] += round(m['message_stats']['publish_details']['rate'], 2)
                healthlog['details']['queues'].append(queueinfo)

        # post to elastic search servers directly without going through
        # message queues in case there is an availability issue
        es.save_object(index=index, body=json.dumps(healthlog))
        # post another doc with a static docid and tag
        # for use when querying for the latest status
        healthlog['tags'] = ['mozdef', 'status', 'latest']
        es.save_object(index=index, doc_id=getDocID(server), body=json.dumps(healthlog))


def initConfig():
    # output our log to stdout or syslog
    options.output = getConfig('output', 'stdout', options.configfile)
    # syslog hostname
    options.sysloghostname = getConfig('sysloghostname',
                                       'localhost',
                                       options.configfile)
    # syslog port
    options.syslogport = getConfig('syslogport', 514, options.configfile)

    # msg queue servers to check in on (list of servernames)
    # message queue server(s) hostname
    options.mqservers = list(getConfig('mqservers',
                                       'localhost',
                                       options.configfile).split(','))
    options.mquser = getConfig('mquser', 'guest', options.configfile)
    options.mqpassword = getConfig('mqpassword', 'guest', options.configfile)
    # port of the rabbitmq json management interface
    options.mqapiport = getConfig('mqapiport', 15672, options.configfile)

    # elastic search server settings
    options.esservers = list(getConfig('esservers',
                                       'http://localhost:9200',
                                       options.configfile).split(','))
    # configure the index to save events to
    options.index = getConfig('index', 'mozdefstate', options.configfile)
    # point to mapping json for the index
    default_mapping_location = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'mozdefStateDefaultMappingTemplate.json')
    options.default_mapping_file = getConfig('default_mapping_file', default_mapping_location, options.configfile)


if __name__ == '__main__':
    parser = OptionParser()
    parser.add_option(
        "-c",
        dest='configfile',
        default=sys.argv[0].replace('.py', '.conf'),
        help="configuration file to use")
    (options, args) = parser.parse_args()
    initConfig()
    main()
