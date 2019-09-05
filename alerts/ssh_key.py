#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# Copyright (c) 2017 Mozilla Corporation

from lib.alerttask import AlertTask
from mozdef_util.query_models import SearchQuery, TermMatch
import re
import os

# This alert consumes data produced by the MIG sshkey module and mig-runner.
# ssh key related events are compared against a whitelist which is the
# alerts configuration file (sshkey.conf). The format of this whitelist
# is as follows:
#
# <host regex> <path>
#
# If a host matches the regex, and the detected key matches the path, the
# alert will not generate an alert event. If the detected key is not in
# the whitelist, an alert will be created.


class SSHKey(AlertTask):
    def __init__(self):
        # _whitelist contains all whitelisted key paths, loaded from the
        # configuration file for the alert plugin
        self._whitelist = []

        AlertTask.__init__(self)
        self._parse_whitelist('ssh_key.conf')

    def main(self):
        search_query = SearchQuery(minutes=30)

        search_query.add_must([
            TermMatch('category', 'event'),
            TermMatch('tags', 'mig-runner-sshkey')
        ])

        self.filtersManual(search_query)

        self.searchEventsSimple()
        self.walkEvents()

    # Load whitelist from file system and store in object, path specifies the
    # path to load the whitelist from
    def _parse_whitelist(self, path):
        full_config_filename = os.path.join(os.path.dirname(__file__), path)
        with open(full_config_filename) as fd:
            lns = [x.strip() for x in fd.readlines()]
            for entry in lns:
                try:
                    pindex = entry.index(' ')
                except ValueError:
                    continue
                self._whitelist.append({
                    'hostre': entry[:pindex],
                    'path': entry[pindex + 1:]
                })

    # Return false if the key path is present in the whitelist, otherwise return
    # true
    def _whitelist_check(self, hostname, privkey):
        for went in self._whitelist:
            try:
                rem = re.compile(went['hostre'])
            except:
                continue
            if rem.match(hostname) is None:
                continue
            if privkey['path'] == went['path']:
                return False
        return True

    def onEvent(self, event):
        # Each event could potentially contain a number of identified private keys, since
        # mig-runner will send an event per host. Compare the private keys in the event
        # to the keys in the whitelist, if any are missing from the whitelist we will include
        # the paths in an alert and return the alert, otherwise no alert is returned.
        ev = event['_source']

        if 'details' not in ev:
            return None
        if 'private' not in ev['details'] or 'agent' not in ev['details']:
            return None
        hostname = ev['details']['agent']
        alertkeys = [x for x in ev['details']['private'] if self._whitelist_check(hostname, x)]
        if len(alertkeys) == 0:
            return None

        category = 'sshkey'
        tags = ['sshkey']
        severity = 'WARNING'
        summary = 'Private keys detected on {} missing from whitelist'.format(hostname)
        ret = self.createAlertDict(summary, category, tags, [event], severity)
        ret['details'] = {
            'private': alertkeys
        }
        return ret
