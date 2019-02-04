#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
# Copyright (c) 2014 Mozilla Corporation


from lib.deadman_alerttask import DeadmanAlertTask
from mozdef_util.query_models import SearchQuery, QueryStringMatch
from mozdef_util.utilities.logger import logger


class AlertDeadmanGeneric(DeadmanAlertTask):

    def main(self):
        self._config = self.parse_json_alert_config('deadman_generic.json')

        for alert_cfg in self._config['alerts']:
            try:
                self.process_alert(alert_cfg)
            except Exception as e:
                logger.exception("Exception received when processing deadman alert ({0}):\n{1}".format(
                    e,
                    alert_cfg.__str__())
                )

    def process_alert(self, alert_config):
        search_query = SearchQuery(minutes=int(alert_config['time_window']))
        search_query.add_must(QueryStringMatch(str(alert_config['search_query'])))
        self.filtersManual(search_query)
        self.searchEventsSimple()
        self.walkEvents(description=alert_config['description'])

    # Set alert properties
    # if no events found
    def onNoEvent(self, description):
        category = 'deadman'
        tags = ['deadman']
        severity = 'ERROR'

        summary = "Deadman check failed for '{0}'".format(description)
        return self.createAlertDict(summary, category, tags, [], severity=severity)
