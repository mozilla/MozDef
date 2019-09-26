#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# Copyright (c) 2015 Mozilla Corporation

import json
import os
import sys
import traceback

from lib.alerttask import AlertTask
from mozdef_util.query_models import SearchQuery, TermMatch, SubnetMatch, QueryStringMatch as QSMatch
from mozdef_util.utilities.logger import logger

import geomodel.alert as alert
import geomodel.config as config
import geomodel.locality as locality


_CONFIG_FILE = os.path.join(
    os.path.dirname(__file__),
    'geomodel_location.json')


class AlertGeoModel(AlertTask):
    '''GeoModel alert runs a set of configured queries for events and
    constructs locality state for users performing authenticated actions.
    When activity is found that indicates a potential compromise of an
    account, an alert is produced.
    '''

    def main(self):
        cfg = self._load_config()

        if not self.es.index_exists('localities'):
            settings = {
                'mappings': {
                    '_doc': {
                        'dynamic_templates': [
                            {
                                'string_fields': {
                                    'mapping': {
                                        'type': 'keyword'
                                    },
                                    'match': '*',
                                    'match_mapping_type': 'string'
                                }
                            },
                        ]
                    }
                }
            }
            self.es.create_index('localities', settings)

        for query_index in range(len(cfg.events)):
            try:
                self._process(cfg, query_index)
            except Exception as err:
                self.error_thrown = err
                traceback.print_exc(file=sys.stdout)
                logger.exception(
                    'Error process events; query=\'{0}\'; error={1}'.format(
                        cfg.events[query_index].lucene_query,
                        err))

    def onAggregation(self, agg):
        username = agg['value']
        events = agg['events']
        cfg = agg['config']

        query = locality.wrap_query(self.es)
        journal = locality.wrap_journal(self.es)

        locs_from_evts = list(filter(
            lambda state: state is not None,
            map(locality.from_event, events)))

        entry_from_es = locality.find(query, username, cfg.localities.es_index)

        new_state = locality.State('locality', username, locs_from_evts)

        if entry_from_es is None:
            entry_from_es = locality.Entry(
                '', locality.State('locality', username, []))

        cleaned = locality.remove_outdated(
            entry_from_es.state, cfg.localities.valid_duration_days)

        # Determine if we should trigger an alert before updating the state.
        new_alert = alert.alert(
            cleaned.state.username,
            new_state.localities,
            cleaned.state.localities)

        updated = locality.update(cleaned.state, new_state)

        if updated.did_update:
            entry_from_es = locality.Entry(entry_from_es.identifier, updated.state)

            journal(entry_from_es, cfg.localities.es_index)

        if new_alert is not None:
            summary = '{} seen in {},{}'.format(
                username,
                new_alert.hops[0].origin.city,
                new_alert.hops[0].origin.country)

            for hop in new_alert.hops:
                summary += ' then {},{}'.format(
                    hop.destination.city, hop.destination.country)

            alert_dict = self.createAlertDict(
                summary, 'geomodel', ['geomodel'], events, 'INFO')

            # TODO: When we update to Python 3.7+, change to asdict(alert_produced)
            alert_dict['details'] = {
                'username': new_alert.username,
                'hops': [dict(hop._asdict()) for hop in new_alert.hops]
            }

            return alert_dict

        return None

    def _process(self, cfg: config.Config, qindex: int):
        evt_cfg = cfg.events[qindex]

        search = SearchQuery(**evt_cfg.search_window)
        search.add_must(QSMatch(evt_cfg.lucene_query))
        # Ignore empty usernames
        search.add_must_not(TermMatch(evt_cfg.username_path, ''))
        # Ignore whitelisted usernames
        for whitelisted_username in cfg.whitelist.users:
            search.add_must_not(TermMatch(evt_cfg.username_path, whitelisted_username))
        # Ignore whitelisted subnets
        for whitelisted_subnet in cfg.whitelist.cidrs:
            search.add_must_not(SubnetMatch('details.sourceipaddress', whitelisted_subnet))

        self.filtersManual(search)
        self.searchEventsAggregated(evt_cfg.username_path, samplesLimit=1000)
        self.walkAggregations(threshold=1, config=cfg)

    def _load_config(self):
        with open(_CONFIG_FILE) as cfg_file:
            cfg = json.load(cfg_file)

            cfg['localities'] = config.Localities(**cfg['localities'])

            cfg['events'] = [
                config.Events(**evt_cfg)
                for evt_cfg in cfg['events']
            ]

            cfg['whitelist'] = config.Whitelist(**cfg['whitelist'])

            return config.Config(**cfg)
