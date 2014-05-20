#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
# Copyright (c) 2014 Mozilla Corporation
#
# Contributors:
# Jeff Bryner jbryner@mozilla.com
# Anthony Verez averez@mozilla.com

# Use this to setup the index templates for mozdef
# You only need to run it once, it will setup the templates
# used as future indexes are created

import requests
import sys
import os
from configlib import getConfig, OptionParser

sys.path.insert(1, os.path.join(sys.path[0], '..'))
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
    es.setupIndexTemplate('eventstemplate', '../examples/es-docs/events_template.json')
    es.setupIndexTemplate('alertstemplate', '../examples/es-docs/alerts_template.json')
