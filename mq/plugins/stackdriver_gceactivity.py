# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# Copyright (c) 2017 Mozilla Corporation

from mozdef_util.utilities.toUTC import toUTC
import os
import yaml
import jmespath


class message(object):
    def __init__(self):
        """
            Plugin used to fix object type discretions with cloudtrail messages
        """
        self.registration = ["stackdriver"]
        self.priority = 16

        with open(os.path.join(os.path.dirname(__file__), "stackdriver_gceactivity.yml"), "r") as f:
            mapping_map = f.read()

        yap = yaml.safe_load(mapping_map)
        self.eventtypes = list(yap.keys())
        self.yap = yap
        del mapping_map

    def onMessage(self, message, metadata):
        if "tags" not in message:
            return (message, metadata)
        if "stackdriver" not in message["tags"]:
            return (message, metadata)
        if "category" not in message:
            return (message, metadata)
        # XXX: move into a config file
        cats = ["gceactivity"]
        if message["category"] not in cats:
            return (message, metadata)

        event = message["details"]

        newmessage = dict()

        newmessage["receivedtimestamp"] = toUTC(message["receivedtimestamp"]).isoformat()
        newmessage["timestamp"] = toUTC(event["timestamp"]).isoformat()
        newmessage["utctimestamp"] = toUTC(event["timestamp"]).isoformat()
        newmessage["category"] = message["category"]
        newmessage["tags"] = message["tags"]
        newmessage["source"] = message["source"]
        newmessage["mozdefhostname"] = message["mozdefhostname"]
        newmessage["customendpoint"] = ""
        newmessage["details"] = {}
        newmessage["details"] = message["details"]
        newmessage["details"]["gceactivity"] = newmessage["details"]["jsonPayload"]
        del newmessage["details"]["jsonPayload"]
        # This is fake
        newmessage["details"]["service"] = "compute.googleapis.com"
        # Stuff fields that will be used as a summary with something, anything. The mapping function will hopefuly find something to overwrite it with.
        newmessage["details"]["username"] = "UNKNOWN"
        newmessage["details"]["resourcename"] = "UNKNOWN"

        if message["category"] in self.eventtypes:
            for key in self.yap[newmessage["category"]]:
                mappedvalue = jmespath.search(self.yap[newmessage["category"]][key], newmessage)
                # JMESPath likes to silently return a None object
                if mappedvalue is not None:
                    newmessage["details"][key] = mappedvalue

        # This is redundant
        newmessage["summary"] = "{0} executed {1} on {2}".format(
            newmessage["details"]["username"], newmessage["details"]["action"], newmessage["details"]["resourcename"],
        )

        return (newmessage, metadata)
