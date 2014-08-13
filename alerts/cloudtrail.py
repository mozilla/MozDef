#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
# Copyright (c) 2014 Mozilla Corporation
#
# Contributors:
# Anthony Verez averez@mozilla.com

from lib.alerttask import AlertTask

class AlertCloudtrail(AlertTask):
    def main(self):
        # look for events in last 160 hours
        date_timedelta = dict(hours=160)
        # Configure filters by importing a kibana dashboard
        self.filtersFromKibanaDash('cloudtrail_dashboard.json', date_timedelta)

        # Search events
        self.searchEventsSimple()
        self.walkEvents()

    # Set alert properties
    def onEvent(self, event):
        category = 'AWSCloudtrail'
        tags = ['cloudtrail','aws']
        severity = 'INFO'

        summary = ('{0} called {1} from {2}'.format(event['_source']['userIdentity']['userName'], event['_source']['eventName'], event['_source']['sourceIPAddress']))
        if event['_source']['eventName'] == 'RunInstances':
            for i in event['_source']['responseElements']['instancesSet']['items']:
                if 'privateDnsName' in i.keys():
                    summary += (' running {0} '.format(i['privateDnsName']))
                elif 'instanceId' in i.keys():
                    summary += (' running {0} '.format(i['instanceId']))
                else:
                    summary += (' running {0} '.format(flattenDict(i)))
        if event['_source']['eventName'] == 'StartInstances':
            for i in event['_source']['requestParameters']['instancesSet']['items']:
                summary += (' starting {0} '.format(i['instanceId']))

        # Create the alert object based on these properties
        return self.createAlertDict(summary, category, tags, [event], severity)