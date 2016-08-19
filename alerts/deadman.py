#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
# Copyright (c) 2014 Mozilla Corporation
#
# Contributors:
# Jeff Bryner jbryner@mozilla.com
#
# a collection of alerts looking for the lack of events
# to alert on a dead input source.

from lib.alerttask import AlertTask
from query_models import SearchQuery, TermMatch, PhraseMatch


def fakeEvent():
    # make a fake event
    # mimicing some parameters since this isn't an ES event
    # but should have an ES event metadata structure
    # like _index, _type, etc.
    event = dict()
    event['_index'] = ''
    event['_type'] = ''
    event['_source'] = dict()
    event['_id'] = ''
    return event


class broNSM(AlertTask):
    def main(self, *args, **kwargs):
        # call with hostlist=['host1','host2','host3']
        # to search for missing events
        if kwargs and 'hostlist' in kwargs.keys():
            for host in kwargs['hostlist']:
                self.log.debug('checking deadman for host: {0}'.format(host))
                search_query = SearchQuery(minutes=20)

                search_query.add_must([
                    PhraseMatch("details.note", "MozillaAlive::Bro_Is_Watching_You"),
                    PhraseMatch("details.peer_descr", host),
                    TermMatch('category', 'bronotice'),
                    TermMatch('_type', 'bro')
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

        summary = ('no {0} bro healthcheck events found since {1}'.format(hostname, self.begindateUTC.isoformat()))
        url = "https://mana.mozilla.org/wiki/display/SECURITY/NSM+IR+procedures"

        # make an event to attach to the alert
        event = fakeEvent()
        # attach our info about not having an event to _source:
        # to mimic an ES document
        event['_source']['category'] = 'deadman'
        event['_source']['tags'] = ['bro']
        event['_source']['severity'] = 'ERROR'
        event['_source']['hostname'] = hostname
        event['_source']['summary'] = summary
        # serialize the filter to avoid datetime objects causing json problems.
        event['_source']['details'] = dict(filter='{0}'.format(self.filter.serialize()))

        # Create the alert object based on these properties
        return self.createAlertDict(summary, category, tags, [event], severity=severity, url=url)
