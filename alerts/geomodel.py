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

import alerts.geomodel.alert as alert 
import alerts.geomodel.config as config
import alerts.geomodel.locality as locality


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
        cfg = agg['config']

        localities = list(filter(map(locality.from_event, events)))
        new_state = locality.State('locality', username, localities)

        query = locality.wrap_query(self.es)
        journal = locality.wrap_journal(self.es)

        entry = locality.find(query, username, cfg.localities.es_index)
        if entry is None:
            entry = locality.Entry(
                '', locality.State('localities', username, []))

        updated = locality.Update.flat_map(
            lambda state: locality.remove_outdated(
                state,
                cfg.localities.valid_duration_days),
            locality.update(entry.state, new_state))

        if updated.did_update:
            entry.state = updated.state

            journal(entry, cfg.localities.es_index)

        alert_produced = alert.alert(entry.state, cfg.alerts.whitelist)

        if alert_produced is not None:
            # TODO: When we update to Python 3.7+, change to asdict(alert_produced)
            return dict(alert_produced._asdict())

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
