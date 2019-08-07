#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# Copyright (c) 2018 Mozilla Corporation

from lib.alerttask import AlertTask, add_hostname_to_ip
from mozdef_util.query_models import SearchQuery, TermMatch, QueryStringMatch, PhraseMatch


class NSMScanPort(AlertTask):
    def __init__(self):
        AlertTask.__init__(self)
        self._config = self.parse_json_alert_config('nsm_scan_port.json')

    def main(self):
        search_query = SearchQuery(minutes=2)
        search_query.add_must([
            TermMatch('category', 'bro'),
            TermMatch('source', 'notice'),
            PhraseMatch('details.note', 'Scan::Port_Scan'),
            QueryStringMatch('details.sourceipaddress: {}'.format(self._config['sourcemustmatch']))
        ])
        search_query.add_must_not([
            QueryStringMatch('details.sourceipaddress: {}'.format(self._config['sourcemustnotmatch']))
        ])
        search_query.add_must_not([
            QueryStringMatch('details.msg: {}'.format(self._config['destinationmustnotmatch']))
        ])

        self.filtersManual(search_query)
        self.searchEventsAggregated('details.sourceipaddress', samplesLimit=10)
        self.walkAggregations(threshold=1)

    def onAggregation(self, aggreg):
        category = 'nsm'
        severity = 'WARNING'
        tags = ['nsm', "bro", 'portscan']

        indicators = 'unknown'
        x = aggreg['events'][0]['_source']
        if 'details' in x:
            if 'indicators' in x['details']:
                indicators = x['details']['sourceipaddress']
                indicators_info = add_hostname_to_ip(indicators, '{0} ({1})', require_internal=False)

        summary = 'Port scan from {}'.format(indicators_info)

        return self.createAlertDict(summary, category, tags, aggreg['events'], severity)
