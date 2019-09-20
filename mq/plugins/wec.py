# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
# Copyright (c) 2017 Mozilla Corporation

import os
import jmespath
import yaml
from mozdef_util.utilities.toUTC import toUTC


class message(object):
    def __init__(self):
        '''
            Plugin used to fix object type discretions with cloudtrail messages
        '''
        self.registration = ['syslog_wef']
        self.priority = 10

        with open(os.path.join(os.path.dirname(__file__), 'wec.yml'), 'r') as f:
            mapping_map = f.read()

        yap = yaml.safe_load(mapping_map)
        self.eventtypes = list(yap.keys())
        self.yap = yap
        del(mapping_map)


    def onMessage(self, message, metadata):

        if 'source' not in message:
            return (message, metadata)
        # Maybe it should be a Channel?
        if message["source"] != "wec-nxlog":
            return (message, metadata)

        newmessage = {}
        newmessage['details'] = {}

        newmessage['category'] = 'windowseventlogs'
        newmessage['tags'] = ['windowseventlogs', 'wec']
        newmessage['eventsource'] = 'wec'

        if "EventTime" in message:
            newmessage["utctimestamp"] = toUTC(message["EventTime"]).isoformat()
        if "Hostname" in message:
            newmessage["hostname"] = message["Hostname"]
        if "SourceName" in message:
            newmessage["source"] = message["SourceName"]
        if "Severity" in message:
            newmessage["severity"] = message["Severity"].upper()
        if "Keywords" in message:
            newmessage["details"]["keywords"] = str(message["Keywords"])
        if "EventType" in message:
            newmessage["details"]["eventtype"] = message["EventType"].lower()
            if message["EventType"] == "AUDIT_SUCCESS":
                newmessage["details"]["success"] = True
            elif message["EventType"] == "AUDIT_FAILURE":
                newmessage["details"]["success"] = False

        if "Message" in message:
            # do not even ask
            msg = message["Message"].replace("\r", " ")
            msg = msg.replace("\n", "")
            msg = msg.replace("\t", "")
            # make it possible to search without wildcards
            msg = msg.replace(":", ": ")
            newmessage["summary"] = msg

        # iterate through top level keys - push, etc
        if newmessage['category'] in self.eventtypes:
            for key in self.yap[newmessage['category']]:
                mappedvalue = jmespath.search(self.yap[newmessage['category']][key], message)
                # JMESPath likes to silently return a None object
                if mappedvalue is not None:
                    newmessage['details'][key] = mappedvalue
        else:
            newmessage = None

        return (newmessage, metadata)
