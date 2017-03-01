#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
# Copyright (c) 2017 Mozilla Corporation
#
# Contributors:
# kang@mozilla.com

# TODO: Dont use query_models, nicer fixes for AlertTask

from lib.alerttask import AlertTask
from query_models import SearchQuery, TermMatch, QueryStringMatch
import json
import sys
import traceback
import glob

class DotDict(dict):
    '''dict.item notation for dict()'s'''
    __getattr__ = dict.__getitem__
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__

    def __init__(self, dct):
        for key, value in dct.items():
            if hasattr(value, 'keys'):
                value = DotDict(value)
            self[key] = value

def debug(msg):
	sys.stderr.write(msg+"\n")

class AlertGenericLoader(AlertTask):
    def load_configs(self):
        '''Load all configured rules'''
        self.configs = []
        files = glob.glob("rules/*.json")
        for f in files:
            with open(f) as fd:
                # XXX Make a nicer try thing
                try:
                    # XXX template the json to get defaults
                    cfg = DotDict(json.load(fd))
                    self.configs.append(cfg)
                except:
                    traceback.print_exc(file=sys.stdout)
                    debug("Loading rule file {} failed".format(f))

    def process_alert(self, config):
        search_query = SearchQuery(minutes=int(config.threshold.timerange_min))
	terms = []
        for i in config.filters:
               terms.append(TermMatch(i[0], i[1]))
	terms.append(QueryStringMatch(str(config.search_string)))
        search_query.add_must(terms)
        self.filtersManual(search_query)
        self.searchEventsAggregated('hostname', samplesLimit=int(config.threshold.count))
        self.walkAggregations(threshold=int(config.threshold.count), config=config)

    def main(self):
        self.load_configs()
        try:
            for cfg in self.configs:
                 self.process_alert(cfg)
        except:
            traceback.print_exc(file=sys.stdout)

    def onAggregation(self, aggreg):
        # aggreg['count']: number of items in the aggregation, ex: number of failed login attempts
        # aggreg['value']: value of the aggregation field, ex: toto@example.com
        # aggreg['events']: list of events in the aggregation
        category = 'generic_alerts'
        tags = aggreg['config']['tags']
        severity = aggreg['config']['likelihood_indicator']

        summary = '{} ({}): {}'.format(aggreg['config']['summary'], aggreg['count'], aggreg['value'])

        return self.createAlertDict(summary, category, tags, aggreg['events'], severity)
