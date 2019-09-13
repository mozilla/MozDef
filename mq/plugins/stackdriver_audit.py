# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# Copyright (c) 2017 Mozilla Corporation

from mozdef_util.utilities.key_exists import key_exists
from mozdef_util.utilities.toUTC import toUTC
from mozdef_util.utilities.dot_dict import DotDict
import os
import yaml
import jmespath
import urllib.parse

# activity for Admin Activity audit logs
# data_access for Data Access audit logs
# system_events for System Event audit logs.
# https://cloud.google.com/logging/docs/api/v2/resource-list

# organization
# project
# timestamp
# authenticationInfo
# logName
# protoPayload.serviceName <- what service wrote the audit log
# protoPayload.methodName <- what operation is being audited
# protoPayload.serviceData <- more information about the operation being audited
# resource.type <- What resource is being audited
# resource.labels.project_id <- What resource is being audited
# details.gaudit.status.code
# details.gaudit.status.message

# GCE activity logs
# set category if jsonPayload in details and logname ends with activity
# move details.jsonPayload somewhere else
# details.jsonPayload.actor.user
# details.jsonPayload.event_subtype
# details.jsonPayload.event_type
# details.jsonPayload.ip_address
# details.logName

# XXX: should I implement a lookup table to map


class message(object):
    def __init__(self):
        """
            Plugin used to fix object type discretions with cloudtrail messages
        """
        self.registration = ["stackdriver"]
        self.priority = 15

        try:
            self.mozdefhostname = "{0}".format(node())
        except:
            self.mozdefhostname = "failed to fetch mozdefhostname"
            pass

        with open(
            os.path.join(os.path.dirname(__file__), "stackdriver_audit.yml"), "r"
        ) as f:
            mapping_map = f.read()

        yap = yaml.safe_load(mapping_map)
        self.eventtypes = list(yap.keys())
        self.yap = yap
        del (mapping_map)

    def onMessage(self, message, metadata):
        if "stackdriver" not in message["tags"]:
            return (message, metadata)
        if "category" not in message:
            return (message, metadata)
        # XXX: move into a config file
        cats = ["activity", "data_access"]
        if message["category"] not in cats:
            return (message, metadata)

        newmessage = dict()

        newmessage["receivedtimestamp"] = toUTC(
            message["receivedtimestamp"]
        ).isoformat()
        newmessage["timestamp"] = toUTC(message["details"]["timestamp"]).isoformat()
        newmessage["utctimestamp"] = toUTC(message["details"]["timestamp"]).isoformat()
        newmessage["category"] = message["category"]
        newmessage["tags"] = message["tags"]
        newmessage["source"] = message["source"]
        newmessage["mozdefhostname"] = message["mozdefhostname"]
        newmessage["customendpoint"] = ""
        newmessage["details"] = {}
        newmessage["details"] = message["details"]
        newmessage["details"]["gaudit"] = newmessage["details"]["protoPayload"]
        del (newmessage["details"]["protoPayload"])
        if "request" in newmessage["details"]["gaudit"]:
            if "resource" in newmessage["details"]["gaudit"]["request"]:
                if (
                    type(newmessage["details"]["gaudit"]["request"]["resource"])
                    is not dict
                ):
                    del (newmessage["details"]["gaudit"]["request"]["resource"])

        todel = set()
        if message["category"] in self.eventtypes:
            for key in self.yap[newmessage["category"]]:
                mappedvalue = jmespath.search(
                    self.yap[newmessage["category"]][key], newmessage
                )
                todel.add(self.yap[newmessage["category"]][key])
                # JMESPath likes to silently return a None object
                if mappedvalue is not None:
                    newmessage[key] = mappedvalue

        return (newmessage, metadata)
