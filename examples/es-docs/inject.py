#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
# Copyright (c) 2014 Mozilla Corporation
#
# Contributors:
# Anthony Verez averez@mozilla.com

import os
import sys
import inspect
from configlib import getConfig, OptionParser

sys.path.insert(1, os.path.join(sys.path[0], '../..'))
from utils import es as es_module


def initConfig():
    options.esservers = list(getConfig(
        'esservers',
        'http://localhost:9200',
        options.configfile).split(',')
    )


if __name__ == '__main__':
    parser = OptionParser()
    parser.add_option("-c",
                      dest='configfile',
                      default=sys.argv[0].replace('.py', '.conf'),
                      help="configuration file to use")
    (options, args) = parser.parse_args()
    initConfig()
    es = es_module.Elasticsearch(options.esservers[0])
    es.deleteIndex('events')
    es.deleteIndex('events-previous')
    es.deleteIndex('alerts')
    es.deleteIndex('kibana-int')
    es.setupIndexTemplate('eventstemplate', 'events_template.json')
    es.setupIndexTemplate('alertstemplate', 'alerts_template.json')
    es.createIndex('alerts')
    es.createIndex('events')
    es.createIndex('events-previous')
    es.loadDocs('events', 'auditd', 'events-auditd.json', True)
    es.loadDocs('events', 'event', 'events-event.json', True)
    es.loadDocs('events', 'cloudtrail', 'events-cloudtrail.json', True)
    es.loadDocs('events', 'event', 'bro_intel.json', True)
    es.loadDocs('events', 'event', 'bro_notice.json', True)
    es.loadDocs('events', 'event', 'bruteforce_ssh.json', True)
    es.loadDocs('events', 'event', 'fail2ban.json', True)

    es.loadDashboard('events', 'events-kibana.json')
    es.loadDashboard('alerts', 'alerts-kibana.json')
