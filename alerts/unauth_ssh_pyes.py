#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
# Copyright (c) 2015 Mozilla Corporation
#
# Contributors:
# Aaron Meihm <ameihm@mozilla.com>

from lib.alerttask import AlertTask
from lib.query_classes import SearchQuery, TermFilter, QueryFilter, QueryStringQuery, MatchQuery
import json
import re
from configlib import getConfig, OptionParser

# Note: this plugin requires a configuration file (unauth_ssh_pyes.conf)
# to exist in the same directory as the plugin.
#
# It should contain content such as:
# [options]
# hostfilter <ES compatible regexp>
# user username
# skiphosts 1.2.3.4 2.3.4.5

class AlertUnauthSSH(AlertTask):
    def main(self):
        self.config_file = './unauth_ssh_pyes.conf'
        self.config = None
        self.initConfiguration()

        search_query = SearchQuery(minutes=30)

        search_query.add_must([
            TermFilter('_type', 'event'),
            TermFilter('category', 'syslog'),
            TermFilter('details.program', 'sshd'),
            QueryFilter(QueryStringQuery('details.hostname: /{}/'.format(self.config.hostfilter))),
            QueryFilter(MatchQuery('summary', 'Accepted publickey {}'.format(self.config.user), operator='and'))
        ])

        for x in self.config.skiphosts:
            search_query.add_must_not(QueryFilter(MatchQuery('summary', x)))

        self.filtersManual(search_query)
        self.searchEventsSimple()
        self.walkEvents()

    def initConfiguration(self):
        myparser = OptionParser()
        (self.config, args) = myparser.parse_args([])
        self.config.hostfilter = getConfig('hostfilter', '', self.config_file)
        self.config.user = getConfig('user', '', self.config_file)
        self.config.skiphosts = getConfig('skiphosts', '', self.config_file).split()

    # Set alert properties
    def onEvent(self, event):
        category = 'unauthaccess'
        tags = ['ssh']
        severity = 'WARNING'

        targethost = 'unknown'
        sourceipaddress = 'unknown'
        x = event['_source']
        if 'details' in x:
            if 'hostname' in x['details']:
                targethost = x['details']['hostname']
            if 'sourceipaddress' in x['details']:
                sourceipaddress = x['details']['sourceipaddress']

        targetuser = 'unknown'
        expr = re.compile('Accepted publickey for ([A-Za-z0-9@.\-]+) from')
        m = expr.match(event['_source']['summary'])
        groups = m.groups()
        if len(groups) > 0:
            targetuser = groups[0]

        summary = 'Unauthorized SSH account usage by {0} on {1} user {2}'.format(sourceipaddress, targethost, targetuser)
        return self.createAlertDict(summary, category, tags, [event], severity)
