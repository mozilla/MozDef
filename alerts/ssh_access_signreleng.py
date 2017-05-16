#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
# Copyright (c) 2015 Mozilla Corporation
#
# Contributors:
# Aaron Meihm <ameihm@mozilla.com>

from lib.alerttask import AlertTask
from query_models import SearchQuery, TermMatch, PhraseMatch, QueryStringMatch
import json
import re
from configlib import getConfig, OptionParser

# Note: this plugin requires a configuration file (ssh_access_signreleng.conf)
# to exist in the same directory as the plugin.
#
# It should contain content such as:
# [options]
# hostfilter <ES compatible regexp>
# user username
# skiphosts 1.2.3.4 2.3.4.5

class AlertAuthSignRelengSSH(AlertTask):
    def main(self):
        search_query = SearchQuery(minutes=15)

        self.config_file = './ssh_access_signreleng.conf'
        self.config = None
        self.initConfiguration()

        search_query.add_must([
            TermMatch('tags', 'releng'),
            TermMatch('details.program', 'sshd'),
            QueryStringMatch('details.hostname: /{}/'.format(self.config.hostfilter)),
            PhraseMatch('summary', 'Accepted publickey for ')
        ])

        for x in self.config.users:
            search_query.add_must_not(PhraseMatch('summary', x))

        self.filtersManual(search_query)
        self.searchEventsSimple()
        self.walkEvents()

    def initConfiguration(self):
        myparser = OptionParser()
        (self.config, args) = myparser.parse_args([])
        self.config.hostfilter = getConfig('hostfilter', '', self.config_file)
        self.config.skiphosts = getConfig('skiphosts', '', self.config_file).split()
        self.config.users = getConfig('users', '', self.config_file).split()

    # Set alert properties
    def onEvent(self, event):
        category = 'access'
        tags = ['ssh']
        severity = 'NOTICE'

        targethost = 'unknown'
        sourceipaddress = 'unknown'
        x = event['_source']
        if 'details' in x:
            if 'hostname' in x['details']:
                targethost = x['details']['hostname']
            if 'sourceipaddress' in x['details']:
                sourceipaddress = x['details']['sourceipaddress']

        targetuser = 'unknown'
        expr = re.compile('Accepted publickey for ([A-Za-z0-9]+) from')
        m = expr.match(event['_source']['summary'])
        groups = m.groups()
        if len(groups) > 0:
            targetuser = groups[0]

        summary = 'SSH login on releng sensitive infrastructure from {0} on {1} as user {2}'.format(sourceipaddress, targethost, targetuser)
        return self.createAlertDict(summary, category, tags, [event], severity)
