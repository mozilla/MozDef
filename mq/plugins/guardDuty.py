# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# Copyright (c) 2017 Mozilla Corporation

import os
import yaml
import jmespath
from mozdef_util.utilities.toUTC import toUTC
from platform import node


class message(object):
    def __init__(self):
        """
            Plugin used to fix object type discretions with cloudtrail messages
        """
        self.registration = ["guardduty"]
        self.priority = 3

        try:
            self.mozdefhostname = "{0}".format(node())
        except:
            self.mozdefhostname = "failed to fetch mozdefhostname"
            pass

        with open(os.path.join(os.path.dirname(__file__), "guardduty_mapping.yml"), "r") as f:
            mapping_map = f.read()

        yap = yaml.safe_load(mapping_map)
        self.eventtypes = list(yap.keys())
        self.yap = yap
        del mapping_map

        # AWS guard duty sends dates as iso_8601 which ES doesn't appreciate
        # here's a list of date fields we'll convert to isoformat
        self.date_keys = ["gdeventcreatedts", "gdeventupdatedts", "gdeventfirstseents", "gdeventlastseents"]

    def onMessage(self, message, metadata):
        if "source" not in message:
            return (message, metadata)

        if not message["source"] == "guardduty":
            return (message, metadata)

        if "details" not in message:
            return (message, metadata)

        newmessage = dict()
        newmessage["receivedtimestamp"] = message["receivedtimestamp"]
        newmessage["timestamp"] = message["timestamp"]
        newmessage["utctimestamp"] = message["utctimestamp"]
        newmessage["mozdefhostname"] = message["mozdefhostname"]
        newmessage["tags"] = ["aws", "guardduty"] + message["tags"]
        newmessage["category"] = "guardduty"
        newmessage["source"] = "guardduty"
        newmessage["customendpoint"] = ""
        newmessage["details"] = {}
        newmessage["details"]["type"] = message["details"]["finding"]["action"]["actionType"].lower()
        newmessage["details"]["finding"] = message['details']["category"]
        newmessage["summary"] = message["details"]["title"]
        newmessage["details"]["resourcerole"] = message["details"]["finding"]["resourceRole"].lower()

        # This is a hack to let the following code match and extract useful information about local network configuration
        # Sometimes AWS does not feel like sending it at all or sends an empty list or a single element list or a multiple-elements list or a dictionary - so try to handle them all
        if message["details"]["finding"]["action"]["actionType"] != "AWS_API_CALL":
            if "networkInterfaces" in message["details"]["resource"]["instanceDetails"]:
                nic = message["details"]["resource"]["instanceDetails"]["networkInterfaces"]
                if isinstance(nic, list):
                    if len(nic) > 0:
                        message["details"]["resource"]["instanceDetails"]["networkInterfaces"] = nic[0]
        if message["details"]["category"] in self.eventtypes:
            for key in self.yap[newmessage["details"]["finding"]]:
                mappedvalue = jmespath.search(self.yap[newmessage["details"]["finding"]][key], message)
                # JMESPath likes to silently return a None object
                if mappedvalue is not None:
                    newmessage["details"][key] = mappedvalue

        # reformat the date fields to isoformat
        for date_key in self.date_keys:
            if date_key in newmessage["details"]:
                newmessage["details"][date_key] = toUTC(newmessage["details"][date_key]).isoformat()

        # Handle some special cases

        # Propagate domain
        if "miscinfo" in newmessage["details"]:
            if "domain" in newmessage["details"]["miscinfo"]:
                newmessage["details"]["query"] = newmessage["details"]["miscinfo"]["domain"]

        # Flatten tags
        if "tags" in newmessage["details"]:
            newmessage["details"]["awstags"] = []
            for tagkve in newmessage["details"]["tags"]:
                for k, v in tagkve.items():
                    newmessage["details"]["awstags"].append(v.lower())
            del newmessage["details"]["tags"]

        # Find something that remotely resembles an FQDN
        if "publicdnsname" in newmessage["details"]:
            newmessage["hostname"] = newmessage["details"]["publicdnsname"]
        elif "privatednsname" in newmessage["details"]:
            newmessage["hostname"] = newmessage["details"]["privatednsname"]

        # Flip IP addresses in we are the source of attacks
        if (newmessage["details"]["finding"] == "UnauthorizedAccess:EC2/RDPBruteForce" or newmessage["details"]["finding"] == "UnauthorizedAccess:EC2/SSHBruteForce"):
            if newmessage["details"]["direction"] == "OUTBOUND":
                # could be more optimized here but need to be careful
                truedstip = "0.0.0.0"
                truesrcip = "0.0.0.0"
                if "destinationipaddress" in newmessage["details"]:
                    truedstip = newmessage["details"]["sourceipaddress"]
                if "sourceipaddress" in newmessage["details"]:
                    truesrcip = newmessage["details"]["destinationipaddress"]
                newmessage["details"]["destinationipaddress"] = truedstip
                newmessage["details"]["sourceipaddress"] = truesrcip
                del newmessage["details"]["sourceport"]
                del newmessage["details"]["destinationport"]

        # Last resort in case we don't have any local IP address yet
        # Fake it till you make it
        attdir = {
            "Recon:EC2/PortProbeUnprotectedPort": "INBOUND",
        }
        if "direction" not in newmessage["details"]:
            newmessage["details"]["direction"] = "INBOUND"
            if newmessage["details"]["finding"] in attdir:
                newmessage["details"]["direction"] = attdir[newmessage["details"]["finding"]]
        if newmessage["details"]["direction"] == "INBOUND":
            if "destinationipaddress" not in newmessage["details"]:
                if "publicip" in newmessage["details"]:
                    newmessage["details"]["destinationipaddress"] = newmessage["details"]["publicip"]
        if newmessage["details"]["direction"] == "OUTBOUND":
            if "sourceipaddress" not in newmessage["details"]:
                if "publicip" in newmessage["details"]:
                    newmessage["details"]["sourceipaddress"] = newmessage["details"]["publicip"]

        return (newmessage, metadata)
