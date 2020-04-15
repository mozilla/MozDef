#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# Copyright (c) 2014 Mozilla Corporation


from lib.deadman_alerttask import DeadmanAlertTask
from mozdef_util.query_models import SearchQuery, QueryStringMatch
from mozdef_util.utilities.logger import logger


class AlertDeadmanGeneric(DeadmanAlertTask):

    def main(self):
        # We override the event indices to search for
        # because our deadman alerts might look past 48 hours
        self.event_indices = ["events-weekly"]

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
        self.current_alert_time_window = int(alert_config['time_window'])
        self.current_alert_time_type = alert_config['time_window_type']
        self.custom_tags = alert_config['tags']
        search_query_time_window = {self.current_alert_time_type: self.current_alert_time_window}
        search_query = SearchQuery(**search_query_time_window)
        search_query.add_must(QueryStringMatch(str(alert_config['search_query'])))
        self.filtersManual(search_query)
        self.searchEventsSimple()
        self.walkEvents(description=alert_config['description'])

    # Set alert properties
    # if no events found
    def onNoEvent(self, description):
        category = 'deadman'
        tags = ['deadman']
        # Allow each definition to specify custom tags
        for custom_tag in self.custom_tags:
            tags.append(custom_tag)

        severity = self._config['severity']

        summary = "Deadman check failed for '{0}' the past {1} {2}".format(
            description,
            self.current_alert_time_window,
            self.current_alert_time_type
        )
        return self.createAlertDict(summary, category, tags, [], severity=severity)
