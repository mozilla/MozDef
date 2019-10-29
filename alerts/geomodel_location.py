#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# Copyright (c) 2015 Mozilla Corporation

import json
import os

from mozdef_util.utilities.toUTC import toUTC
from datetime import datetime, timedelta

from lib.alerttask import AlertTask
from mozdef_util.query_models import\
    SearchQuery,\
    TermMatch,\
    RangeMatch,\
    SubnetMatch,\
    QueryStringMatch as QSMatch

import geomodel.alert as alert
import geomodel.config as config
import geomodel.execution as execution
import geomodel.locality as locality


_CONFIG_FILE = os.path.join(
    os.path.dirname(__file__),
    'geomodel_location.json')

# The ES index in which we record the last time this alert was run.
_EXEC_INDEX = 'localities'

# We expect that, no matter what query GeoModel is configured to run that the
# usernames of users taking actions represented by events retrieved will be
# stored in `event['_source']['details']['username']`.
USERNAME_PATH = 'details.username'


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

        last_execution_record = execution.load(self.es)(_EXEC_INDEX)

        if last_execution_record is None:
            cfg_offset = timedelta(**cfg.events.search_window)
            range_start = toUTC(datetime.now()) - cfg_offset
        else:
            range_start = last_execution_record.state.execution_time

        range_end = toUTC(datetime.now())

        query = SearchQuery()
        query.add_must(RangeMatch('receivedtimestamp', range_start, range_end))
        query.add_must(QSMatch(cfg.events.lucene_query))

        # Ignore empty usernames
        query.add_must_not(TermMatch(USERNAME_PATH, ''))

        # Ignore whitelisted usernames
        for whitelisted_username in cfg.whitelist.users:
            query.add_must_not(TermMatch(USERNAME_PATH, whitelisted_username))

        # Ignore whitelisted subnets
        for whitelisted_subnet in cfg.whitelist.cidrs:
            query.add_must_not(SubnetMatch('details.sourceipaddress', whitelisted_subnet))

        self.filtersManual(query)
        self.searchEventsAggregated(USERNAME_PATH, samplesLimit=1000)
        self.walkAggregations(threshold=1, config=cfg)

        if last_execution_record is None:
            updated_exec = execution.Record.new(
                execution.ExecutionState.new(range_end))
        else:
            updated_exec = execution.Record(
                last_execution_record.identifier,
                execution.ExecutionState.new(range_end))

        execution.store(self.es)(updated_exec, _EXEC_INDEX)

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
            summary = alert.summary(new_alert)

            alert_dict = self.createAlertDict(
                summary, 'geomodel', ['geomodel'], events, 'WARNING')

            # TODO: When we update to Python 3.7+, change to asdict(alert_produced)
            alert_dict['details'] = {
                'username': new_alert.username,
                'hops': [dict(hop._asdict()) for hop in new_alert.hops]
            }

            return alert_dict

        return None

    def _load_config(self):
        with open(_CONFIG_FILE) as cfg_file:
            cfg = json.load(cfg_file)

            cfg['localities'] = config.Localities(**cfg['localities'])

            cfg['events'] = config.Events(**cfg['events'])

            cfg['whitelist'] = config.Whitelist(**cfg['whitelist'])

            return config.Config(**cfg)
