# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
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
        takes an incoming bro message
        and sets the doc_type
        """

        self.registration = ["squid"]
        self.priority = 5
        try:
            self.mozdefhostname = u"{0}".format(node())
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
        if u"customendpoint" not in message:
            return message, metadata
        if u"category" not in message:
            return message, metadata
        if message["category"] != "proxy":
            return message, metadata

        # Reuse the NSM doc type
        # to avoid data type conflicts with other doc types
        # (int v string, etc)
        # index holds documents of type 'type'
        # index -> type -> doc
        metadata["doc_type"] = "nsm"

        # move Squid specific fields under 'details' while preserving metadata
        newmessage = dict()

        newmessage[u"mozdefhostname"] = self.mozdefhostname
        newmessage["details"] = {}

        # move some fields that are expected at the event 'root' where they belong
        if "HOST_FROM" in message:
            newmessage["hostname"] = message["HOST_FROM"]
        if "TAGS" in message:
            newmessage["tags"] = message["tags"]
        if "category" in message:
            newmessage["category"] = message["category"]
        newmessage[u"customendpoint"] = message["customendpoint"]
        newmessage[u"source"] = u"unknown"
        if "source" in message:
            newmessage[u"source"] = message["source"]

            if newmessage["source"] == "access":
                # http://www.squid-cache.org/Doc/config/logformat/
                # https://wiki.squid-cache.org/Features/LogFormat
                # logformat squid %ts.%03tu %6tr %>a %>p %<a %<p %Ss %<Hs %>st %<st %rm %ru %>rs %<A %mt
                line = message["MESSAGE"].strip()
                tokens = line.split()

                newmessage[u"details"][u"duration"] = float(tokens[1]) / 1000.0
                newmessage[u"details"][u"sourceipaddress"] = tokens[2]
                newmessage[u"details"][u"sourceport"] = int(self.create_int(tokens[3]))
                if self.isIPv4(tokens[4]):
                    newmessage[u"details"][u"destinationipaddress"] = tokens[4]
                else:
                    newmessage[u"details"][u"destinationipaddress"] = u"0.0.0.0"
                newmessage[u"details"][u"proxyaction"] = tokens[6]
                if newmessage[u"details"][u"proxyaction"] != "TCP_DENIED":
                    newmessage[u"details"][u"destinationport"] = int(tokens[5])
                    newmessage[u"details"][u"host"] = tokens[13]
                else:
                    (fqdn, dstport) = self.tokenize_url(tokens[11])
                    newmessage[u"details"][u"destinationport"] = dstport
                    newmessage[u"details"][u"host"] = fqdn
                newmessage[u"details"][u"status"] = tokens[7]
                newmessage[u"details"][u"requestsize"] = int(tokens[8])
                newmessage[u"details"][u"responsesize"] = int(tokens[9])
                method = tokens[10]
                newmessage[u"details"][u"method"] = method
                newmessage[u"details"][u"destination"] = tokens[11]
                proto = tokens[12]
                if proto == "-" and method == "CONNECT":
                    proto = "ssl"
                newmessage[u"details"][u"proto"] = proto
                newmessage[u"details"][u"mimetype"] = tokens[14]
                newmessage[u"utctimestamp"] = (
                    toUTC(float(tokens[0])) - timedelta(milliseconds=float(tokens[1]))
                ).isoformat()
                newmessage[u"timestamp"] = (
                    toUTC(float(tokens[0])) - timedelta(milliseconds=float(tokens[1]))
                ).isoformat()

        # add mandatory fields
        newmessage[u"receivedtimestamp"] = toUTC(datetime.now()).isoformat()
        newmessage[u"eventsource"] = u"squid"
        newmessage[u"severity"] = u"INFO"

        return (newmessage, metadata)
