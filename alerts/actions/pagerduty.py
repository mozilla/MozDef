# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# Copyright (c) 2014 Mozilla Corporation

import requests
import hjson
import os

from mozdef_util.utilities.logger import logger


class message(object):
    def __init__(self):
        '''
        takes an incoming alert
        and uses it to trigger an event using
        the pager duty event api
        '''

        self.configfile = os.path.join(os.path.dirname(__file__), 'pagerduty.json')
        self.options = None
        if os.path.exists(self.configfile):
            self.initConfiguration()

        self.registration = [integration['tag'] for integration in self.options['integrations']]
        self.priority = 1

    def initConfiguration(self):
        with open(self.configfile, "r") as fd:
            try:
                self.options = hjson.load(fd)
            except ValueError:
                logger.error("FAILED to open the configuration file\n")

    def identify_option(self, tags):
        for integration_option in self.options['integrations']:
            for tag in tags:
                if tag == integration_option['tag']:
                    return integration_option

    def onMessage(self, alert):
        source = alert['_source']

        # Find the self.option that contains one of the message tags
        selected_option = self.identify_option(source['tags'])
        if selected_option is None:
            logger.error("Unable to find config option for alert tags: {0}".format(source['tags']))

        if 'summary' in source:
            headers = {
                'Content-type': 'application/json',
            }
            payload = hjson.dumps({
                "service_key": "{0}".format(selected_option['service_key']),
                "event_type": "trigger",
                "description": "{0}".format(source['summary']),
                "client": "MozDef",
                "client_url": "https://" + self.options['web_url'] + "/{0}".format(alert['_id']),
                "contexts": [
                    {
                        "type": "link",
                        "href": "https://" + "{0}".format(selected_option['doc']),
                        "text": "View runbook on mana"
                    }
                ]
            })
            requests.post(
                'https://events.pagerduty.com/generic/2010-04-15/create_event.json',
                headers=headers,
                data=payload,
            )

        return message
