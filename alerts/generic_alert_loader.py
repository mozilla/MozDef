#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# Copyright (c) 2017 Mozilla Corporation

# TODO: Dont use query_models, nicer fixes for AlertTask

from lib.alerttask import AlertTask
from mozdef_util.query_models import SearchQuery, TermMatch, QueryStringMatch
from mozdef_util.utilities.dot_dict import DotDict
from mozdef_util.utilities.logger import logger
import hjson
import sys
import traceback
import glob
import os
from os.path import basename

# Minimum data needed for an alert (this is an example alert json)
'''
    {
        // Lucene search string
        'search_string': 'field1: matchingvalue and field2: matchingothervalue',

        // ES Filters as such: [['field', 'value'], ['field', 'value']]
        'filters': [],

        // What to aggregate on if we get multiple matches?
        'aggregation_key': 'summary',

        // Number of minutes from current time to look for events
        "time_window": 5,

        // Max number of samples to include in alert
        // If the total number of events is less than this, the alert
        // will still throw
        "num_samples": 10,

        // Total number of different type of values from aggregation key
        "num_aggregations": 1,

        // This is the category that will show up in mozdef, and the severity
        'alert_category': 'generic_alerts',
        'alert_severity': 'INFO',

        // This will show up as the alert text when it trigger
        'alert_summary': 'Example summary that shows up in the alert',

        // This helps sorting out alerts, so it's nice if you fill this in
        'alert_tags': ['generic'],

        // This is the alert documentation
        'alert_url': 'https://mozilla.org'

        // Optional string field to define which channel the alert goes to (mozdefbot)
        //   Default - set to main channel set in lib/config.py
        'channel': 'testchannel',

        // Optional boolean field if mozdefbot should notify the alert
        //   Default - is determined via severity and if channel is defined
        'notify_mozdefbot': true,

        // Optional field to include other fields (if they exist in each event) in summary
        'additional_summary_fields': [
            'field1',
            'field2'
        ]
    }
'''


class AlertGenericLoader(AlertTask):
    required_fields = [
        "search_string",
        "filters",
        "aggregation_key",
        "time_window",
        "num_samples",
        "num_aggregations",
        "alert_category",
        "alert_tags",
        "alert_severity",
        "alert_summary",
        "alert_url",
    ]

    def validate_alert(self, alert):
        for key in self.required_fields:
            if key not in alert:
                logger.error('Your alert does not have the required field {}'.format(key))
                raise KeyError

    def load_configs(self):
        '''Load all configured rules'''
        self.configs = []
        rules_location = os.path.join(self.config.alert_data_location, "rules")
        files = glob.glob(rules_location + "/*.json")
        for f in files:
            with open(f) as fd:
                try:
                    cfg = DotDict(hjson.load(fd))
                    self.validate_alert(cfg)
                    # We set the alert name to the filename (excluding .json)
                    alert_name = basename(f).replace('.json', '')
                    cfg['custom_alert_name'] = alert_name
                    self.configs.append(cfg)
                except Exception:
                    logger.error("Loading rule file {} failed".format(f))

    def process_alert(self, alert_config):
        # Set instance variable to populate event attributes about an alert
        self.custom_alert_name = "{0}:{1}".format(self.classname(), alert_config['custom_alert_name'])
        search_query = SearchQuery(minutes=int(alert_config.time_window))
        terms = []
        for i in alert_config.filters:
            terms.append(TermMatch(i[0], i[1]))
        terms.append(QueryStringMatch(str(alert_config.search_string)))
        search_query.add_must(terms)
        self.filtersManual(search_query)
        self.searchEventsAggregated(alert_config.aggregation_key, samplesLimit=int(alert_config.num_samples))
        self.walkAggregations(threshold=int(alert_config.num_aggregations), config=alert_config)

    def main(self):
        self.parse_config('generic_alert_loader.conf', ['alert_data_location'])

        self.load_configs()
        for cfg in self.configs:
            try:
                self.process_alert(cfg)
            except Exception as err:
                self.error_thrown = err
                traceback.print_exc(file=sys.stdout)
                logger.exception("Processing rule file {} failed".format(cfg.__str__()))

    def onAggregation(self, aggreg):
        # aggreg['count']: number of items in the aggregation, ex: number of failed login attempts
        # aggreg['value']: value of the aggregation field, ex: toto@example.com
        # aggreg['events']: list of events in the aggregation
        category = aggreg['config']['alert_category']
        tags = aggreg['config']['alert_tags']
        severity = aggreg['config']['alert_severity']
        url = aggreg['config']['alert_url']

        # Find all affected hosts
        # Normally, the hostname data is in e.hostname so try that first,
        # but fall back to e.hostname if it is missing, or nothing at all if there's no hostname! ;-)
        hostnames = []
        for e in aggreg['events']:
            event_source = e['_source']
            if 'hostname' in event_source:
                hostnames.append(event_source['hostname'])

        summary = '{} ({}): {}'.format(
            aggreg['config']['alert_summary'],
            aggreg['count'],
            aggreg['value'],
        )

        channel = None
        # If our generic alert contains channel, use that
        if 'channel' in aggreg['config']:
            channel = aggreg['config']['channel']

        notify_mozdefbot = None
        # If our generic alert explicitly sets if we should notify mozdefbot
        if 'notify_mozdefbot' in aggreg['config']:
            notify_mozdefbot = aggreg['config']['notify_mozdefbot']

        # If additional summary fields is defined, loop through each
        # and pull out the value from each event (if it exists)
        # and append key=value(s) to the summary field
        if 'additional_summary_fields' in aggreg['config']:
            for additional_field in aggreg['config']['additional_summary_fields']:
                values_found = []
                # If the field exists in each EVENT, include it in alert summary
                for event in aggreg['events']:
                    dot_event = DotDict(event['_source'])
                    value = dot_event.get(additional_field)
                    if value:
                        values_found.append(value)
                # Let's add the key=value(s) to summary
                if len(values_found) != 0:
                    values_str = '{}'.format(', '.join(set(values_found)))
                    summary += " ({0}={1})".format(additional_field, values_str)

        if hostnames:
            summary += ' [{}]'.format(', '.join(set(hostnames)))

        return self.createAlertDict(summary, category, tags, aggreg['events'], severity, url, channel=channel, notify_mozdefbot=notify_mozdefbot)
