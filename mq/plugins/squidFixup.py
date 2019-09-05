# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# Copyright (c) 2018 Mozilla Corporation
# http://www.squid-cache.org/Doc/config/logformat/
# https://wiki.squid-cache.org/Features/LogFormat

from datetime import datetime, timedelta
from platform import node
from mozdef_util.utilities.toUTC import toUTC
import tldextract
from netaddr import valid_ipv4


class message(object):
    def __init__(self):
        """
        takes an incoming squid event
        and parses the message to extract
        data points, and sets the type
        field
        """

        self.registration = ["squid"]
        self.priority = 5
        try:
            self.mozdefhostname = "{0}".format(node())
        except:
            self.mozdefhostname = "failed to fetch mozdefhostname"
            pass

    def isIPv4(self, ip):
        try:
            return valid_ipv4(ip)
        except:
            return False

    def create_int(self, field):
        if field == "-":
            field = 0
        return field

    def tokenize_url(self, field):
        field = field.strip()
        tokens = field.split(":")

        offset = 0
        if tokens[0] == "http":
            offset = 1
            dstport = 80
            if len(tokens) > 2:
                inttokens = tokens[2].split("/")
                dstport = int(inttokens[0])
        elif tokens[0] == "https":
            dstport = 443
        else:
            if tokens[-1] is not None:
                dstport = int(tokens[-1])

        tld = tldextract.extract(tokens[offset])
        fqdn = ".".join(part for part in tld if part)

        return (fqdn, dstport)

    def onMessage(self, message, metadata):

        # make sure I really wanted to see this message
        # bail out early if not
        if "customendpoint" not in message:
            return message, metadata
        if "category" not in message:
            return message, metadata
        if message["category"] != "proxy":
            return message, metadata

        # move Squid specific fields under 'details' while preserving metadata
        newmessage = dict()

        # Set NSM as type for categorical filtering of events.
        newmessage["type"] = "squid"

        newmessage["mozdefhostname"] = self.mozdefhostname
        newmessage["details"] = {}

        # move some fields that are expected at the event 'root' where they belong
        if "HOST_FROM" in message:
            newmessage["hostname"] = message["HOST_FROM"]
        if "TAGS" in message:
            newmessage["tags"] = message["tags"]
        if "category" in message:
            newmessage["category"] = message["category"]
        newmessage["customendpoint"] = message["customendpoint"]
        newmessage["source"] = "unknown"
        if "source" in message:
            newmessage["source"] = message["source"]
        if "MESSAGE" in message:
            newmessage["summary"] = message["MESSAGE"]

            if newmessage["source"] == "access":
                # http://www.squid-cache.org/Doc/config/logformat/
                # https://wiki.squid-cache.org/Features/LogFormat
                # logformat squid %ts.%03tu %6tr %>a %>p %<a %<p %Ss %<Hs %>st %<st %rm %ru %>rs %<A %mt
                line = message["MESSAGE"].strip()
                tokens = line.split()

                newmessage["details"]["duration"] = float(tokens[1]) / 1000.0
                newmessage["details"]["sourceipaddress"] = tokens[2]
                newmessage["details"]["sourceport"] = int(self.create_int(tokens[3]))
                if self.isIPv4(tokens[4]):
                    newmessage["details"]["destinationipaddress"] = tokens[4]
                else:
                    newmessage["details"]["destinationipaddress"] = "0.0.0.0"
                newmessage["details"]["proxyaction"] = tokens[6]
                if newmessage["details"]["proxyaction"] != "TCP_DENIED":
                    newmessage["details"]["destinationport"] = int(self.create_int(tokens[5]))
                    newmessage["details"]["host"] = tokens[13]
                else:
                    (fqdn, dstport) = self.tokenize_url(tokens[11])
                    newmessage["details"]["destinationport"] = dstport
                    newmessage["details"]["host"] = fqdn
                newmessage["details"]["status"] = tokens[7]
                newmessage["details"]["requestsize"] = int(tokens[8])
                newmessage["details"]["responsesize"] = int(tokens[9])
                method = tokens[10]
                newmessage["details"]["method"] = method
                newmessage["details"]["destination"] = tokens[11]
                proto = tokens[12]
                if proto == "-" and method == "CONNECT":
                    proto = "ssl"
                newmessage["details"]["proto"] = proto
                newmessage["details"]["mimetype"] = tokens[14]
                newmessage["utctimestamp"] = (
                    toUTC(float(tokens[0])) - timedelta(milliseconds=float(tokens[1]))
                ).isoformat()
                newmessage["timestamp"] = (
                    toUTC(float(tokens[0])) - timedelta(milliseconds=float(tokens[1]))
                ).isoformat()

        # add mandatory fields
        newmessage["receivedtimestamp"] = toUTC(datetime.now()).isoformat()
        newmessage["eventsource"] = "squid"
        newmessage["severity"] = "INFO"

        return (newmessage, metadata)
