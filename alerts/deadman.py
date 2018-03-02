#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
# Copyright (c) 2017 Mozilla Corporation
#
# a collection of alerts looking for the lack of events
# to alert on a dead input source.

from lib.alerttask import AlertTask
from query_models import SearchQuery, TermMatch, PhraseMatch


class broNSM(AlertTask):
    def main(self, *args, **kwargs):
        self.parse_config('deadman.conf', ['url'])
        # call with hostlist=['host1','host2','host3']
        # to search for missing events
        if kwargs and 'hostlist' in kwargs.keys():
            for host in kwargs['hostlist']:
                self.log.debug('checking deadman for host: {0}'.format(host))
                search_query = SearchQuery(minutes=20)

                search_query.add_must([
                    PhraseMatch("details.note", "MozillaAlive::Bro_Is_Watching_You"),
                    PhraseMatch("details.peer_descr", host),
                    TermMatch('category', 'bro'),
                    TermMatch('source', 'notice'),
                ])

                self.filtersManual(search_query)

                # Search events
                self.searchEventsSimple()
                self.walkEvents(hostname=host)

    # Set alert properties
    # if no events found
    def onNoEvent(self, hostname):
        category = 'deadman'
        tags = ['bro']
        severity = 'ERROR'

        summary = ('No {0} bro healthcheck events found the past 20 minutes'.format(hostname))
        url = self.config.url

        # Create the alert object based on these properties
        return self.createAlertDict(summary, category, tags, [], severity=severity, url=url)
