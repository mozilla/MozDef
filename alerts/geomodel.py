#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# Copyright (c) 2015 Mozilla Corporation

import json
import sys
import traceback
j
from lib.alerttask import AlertTask
from mozdef_util.utilities.logger import logger

import alerts.geomodel.config as config


_CONFIG_FILE = './geomodel.json'


class AlertGeoModel(AlertTask):
    '''GeoModel alert runs a set of configured queries for events and
    constructs locality state for users performing authenticated actions.
    When activity is found that indicates a potential compromise of an
    account, an alert is produced.
    '''
    
    def main(self):
        cfg = self._load_config()

        for query_index in range(len(cfg.events)):
            try:
                self._process(cfg, query_index)
            except Exception as err:
                traceback.print_exc(file=sys.stdout)
                logger.error(
                    'Error process events; query="{0}"; error={1}'.format(
                        cfg.events[query_index].lucene_query,
                        err.message))

    def onAggregation(self, agg):
        username = agg['value']
        events = agg['events']

        return None

    def _process(self, cfg: config.Config, qindex: int):
        evt_cfg = cfg.events[qindex]

        search = SearchQuery(minutes=evt_cfg.search_window.minutes)
        search.add_must(QSMatch(evt_cfg.lucene_query))

        self.filtersManual(search)
        self.searchEventsAggregated(evt_cfg.username_path, samplesLimit=1)
        self.walkAggregations(threshold=1, config=cfg)

    def _load_config(self):
        with open(_CONFIG_FILE) as cfg_file:
            cfg = json.load(cfg_file)

            cfg['localities'] = [
                config.Localities(**dat)
                for dat in cfg['localities']
            ]
            cfg['events']['search_window'] = config.SearchWindow(
                **cfg['events']['search_window'])
            cfg['events']['queries'] = [
                config.QuerySpec(**dat)
                for dat in cfg['events']['queries']
            ]
            cfg['events'] = [
                config.Events(**dat)
                for dat in cfg['events']
            ]
            cfg['alerts']['whitelist'] = config.Whitelist(
                **cfg['alerts']['whitelist'])
            cfg['alerts'] = [
                config.Alerts(**dat)
                for dat in cfg['alerts']
            ]

            return config.Config(**cfg)

'''
from lib.alerttask import AlertTask
from mozdef_util.query_models import SearchQuery, TermMatch


class AlertGeomodel(AlertTask):
    # The minimum event severity we will create an alert for
    MINSEVERITY = 2

    def main(self):
        self.parse_config('geomodel.conf', ['exclusions', 'url'])

        search_query = SearchQuery(minutes=30)

        search_query.add_must([
            TermMatch('category', 'geomodelnotice')
        ])

        # Allow the ability to ignore certain users
        for exclusion in self.config.exclusions.split(','):
            search_query.add_must_not(TermMatch('summary', exclusion))

        self.filtersManual(search_query)
        self.searchEventsSimple()
        self.walkEvents()

    # Set alert properties
    def onEvent(self, event):
        category = 'geomodel'
        tags = ['geomodel']
        severity = 'NOTICE'

        ev = event['_source']

        # If the event severity is below what we want, just ignore
        # the event.
        if 'details' not in ev or 'severity' not in ev['details']:
            return None
        if ev['details']['severity'] < self.MINSEVERITY:
            return None

        # By default we assign a MozDef severity of NOTICE, but up this if the
        # geomodel alert is sev 3
        if ev['details']['severity'] == 3:
            severity = 'WARNING'

        summary = ev['summary']
        alert_dict = self.createAlertDict(summary, category, tags, [event], severity, self.config.url)

        if 'category' in ev['details'] and ev['details']['category'].lower() == 'newcountry':
            alert_dict['details'] = {
                'previous_locality_details': ev['details']['prev_locality_details'],
                'locality_details': ev['details']['locality_details'],
                'category': ev['details']['category'],
                'principal': ev['details']['principal'],
                'source_ip': ev['details']['source_ipv4']
            }

        return alert_dict
'''
