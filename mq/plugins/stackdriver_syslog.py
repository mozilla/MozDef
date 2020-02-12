# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# Copyright (c) 2017 Mozilla Corporation

from mozdef_util.utilities.toUTC import toUTC


class message(object):
    def __init__(self):
        """
            Plugin used to fix object type discretions with cloudtrail messages
        """
        self.registration = ["stackdriver"]
        self.priority = 15

    def onMessage(self, message, metadata):
        if "tags" not in message:
            return (message, metadata)
        if "stackdriver" not in message["tags"]:
            return (message, metadata)
        if "category" not in message:
            return (message, metadata)
        if message["category"] != "syslog":
            return (message, metadata)

        event = message["details"]
        newmessage = dict()

        newmessage["receivedtimestamp"] = toUTC(message["receivedtimestamp"]).isoformat()
        newmessage["timestamp"] = toUTC(event["timestamp"]).isoformat()
        newmessage["utctimestamp"] = toUTC(event["timestamp"]).isoformat()
        newmessage["category"] = "syslog"
        newmessage["tags"] = message["tags"]
        newmessage["source"] = message["source"]
        newmessage["mozdefhostname"] = message["mozdefhostname"]
        newmessage["customendpoint"] = ""
        if "facility" in event:
            newmessage["facility"] = event["facility"]
        if "severity" in event:
            newmessage["severity"] = event["severity"]

        line = event["textPayload"].split()
        newmessage["hostname"] = line[3]
        newmessage["processname"] = line[4].strip(":")
        newmessage["summary"] = " ".join(line[5:])

        return (newmessage, metadata)
