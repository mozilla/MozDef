#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
# Copyright (c) 2014 Mozilla Corporation
#
# Contributors:
# Anthony Verez averez@mozilla.com

# Discover indices to create a backup config file

import sys
from datetime import datetime
from datetime import date
from datetime import timedelta
from configlib import getConfig, OptionParser, setConfig
import pyes
import re

def discover():
    es = pyes.ES(server=(list('{0}'.format(s) for s in options.esservers)))
    indicesManager = pyes.managers.Indices(es)
    indices = indicesManager.get_indices()
    config_indices = []
    config_dobackup = []
    config_rotation = []
    config_pruning = []
    for index in indices.keys():
        index_template = index
        freq = 'none'
        pruning = '0'
        if re.search(r'-[0-9]{8}', index):
            freq = 'daily'
            pruning = '20'
            index_template = index[:-9]
        elif re.search(r'-[0-9]{6}', index):
            freq = 'monthly'
            index_template = index[:-7]
        if index_template not in config_indices:
            config_indices.append(index_template)
            config_dobackup.append('1')
            config_rotation.append(freq)
            config_pruning.append(pruning)
    setConfig('backup_indices', ','.join(config_indices), options.configfile)
    setConfig('backup_dobackup', ','.join(config_dobackup), options.configfile)
    setConfig('backup_rotation', ','.join(config_rotation), options.configfile)
    setConfig('backup_pruning', ','.join(config_pruning), options.configfile)

def initConfig():
    options.esservers = list(getConfig(
        'esservers',
        'http://localhost:9200',
        options.configfile).split(',')
        )
    options.indices = list(getConfig(
        'backup_indices',
        'events,alerts,kibana-int',
        options.configfile).split(',')
        )
    options.dobackup = list(getConfig(
        'backup_dobackup',
        '1,1,1',
        options.configfile).split(',')
        )
    options.rotation = list(getConfig(
        'backup_rotation',
        'daily,monthly,none',
        options.configfile).split(',')
        )
    options.pruning = list(getConfig(
        'backup_pruning',
        '20,0,0',
        options.configfile).split(',')
        )

if __name__ == '__main__':
    parser = OptionParser()
    defaultconfigfile = sys.argv[0].replace('.py', '.conf')
    parser.add_option("-c",
                      dest='configfile',
                      default=defaultconfigfile,
                      help="configuration file to use")
    (options, args) = parser.parse_args()
    initConfig()
    discover()