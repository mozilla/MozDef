import os
import sys
import jmespath
import logging
import mozdef_client as mozdef
from yaml import load
from re import compile
from mozdef_util.utilities.toUTC import toUTC
from netaddr import EUI, mac_bare, NotRegisteredError
from datetime import datetime
from mozdef_util.elasticsearch_client import ElasticsearchClient
from mozdef_util.query_models import TermMatch, SearchQuery, QueryStringMatch
from mozdef_util.utilities.logger import logger, initLogger
from configlib import getConfig, OptionParser
from logging.handlers import SysLogHandler
from socket import gethostname
from hashlib import md5
import json

# https://community.arubanetworks.com/t5/AAA-NAC-Guest-Access-BYOD/ClearPass-Error-Codes/ta-p/260799


class RingBuffer:
    def __init__(self, size):
        self.data = [None for i in xrange(size)]

    def append(self, x):
        self.data.pop(0)
        self.data.append(x)

    def get(self):
        return self.data


class UsernameNetResolve:
    def __init__(self):
        self.initParser()
        self.initConfig()
        initLogger(self.options)
        logger.info("started")
        self.initYap()
        self.macassignments = self.readOUIFile()
        self.esClient = ElasticsearchClient(self.options.esreadurl)
        self.es = ElasticsearchClient(self.options.eswriteurl)
        es.create_index("intelligence", ignore_fail=True)
        self.seenRing = RingBuffer(1000)
        self.mypid = os.getpid()
        self.myname = sys.argv[0]
        self.hostname = gethostname()

    def initConfig(self):
        self.options.output = getConfig("output", "stdout", self.options.configfile)
        self.options.esreadurl = getConfig(
            "esreadurl", "localhost:9200", self.options.configfile
        )
        self.options.eswriteurl = getConfig(
            "eswriteurl", "localhost:9200", self.options.configfile
        )
        self.options.cpmap = getConfig("cpmap", "<empty>", self.options.configfile)
        self.options.dhcpexclude = getConfig(
            "dhcpexclude", "<empty>", self.options.configfile
        )

    def initParser(self):
        parser = OptionParser()
        parser.add_option(
            "-c",
            dest="configfile",
            default=sys.argv[0].replace(".py", ".conf"),
            help="configuration file to use",
        )
        (self.options, args) = parser.parse_args()

    def initYap(self):
        with open(
            os.path.join(os.path.dirname(__file__), self.options.cpmap), "r"
        ) as f:
            map = f.read()

        self.yap = load(map)
        del (map)

    def readOUIFile(self):
        """
        Expects the OUI file from IEEE:
        wget http://www.ieee.org/netstorage/standards/oui.txt
        Reads the (hex) line and extracts the hex prefix and the vendor name
        to store as part of the intelligence record about what device the user
        was seen using.
        """
        ouifilename = "oui.txt"
        with open(ouifilename) as ouifile:
            macassignments = {}
            for i in ouifile.readlines()[0::]:
                i = i.strip()
                if "(hex)" in i:
                    fields = i.split("\t")
                    macprefix = fields[0][0:8].replace("-", ":").lower()
                    entity = fields[2]
                    macassignments[macprefix] = entity
        logger.info("The MAC OUI database loaded - %s entries", len(macassignments))
        return macassignments

    def find_mac_by_ip(self):
        ip = compile(
            "(([2][5][0-5]\.)|([2][0-4][0-9]\.)|([0-1]?[0-9]?[0-9]\.)){3}"
            + "(([2][5][0-5])|([2][0-4][0-9])|([0-1]?[0-9]?[0-9]))"
        )
        mac = compile("([a-fA-F0-9]{2}[:|\-]?){6}")

        search_query = SearchQuery(hours=8)
        search_query.add_must(
            [
                TermMatch("category", "syslog"),
                TermMatch("processname", "dhcpd"),
                QueryStringMatch("summary: DHCPOFFER"),
            ]
        )
        for de in self.options.dhcpexclude.split(" "):
            search_query.add_must_not([TermMatch("hostname", de)])
        events = search_query.execute(self.esClient, indices=["events"])

        for event in events["hits"]:
            try:
                match_ip = ip.search(event["_source"]["summary"]).group()
            except:
                pass
            try:
                match_mac = mac.search(event["_source"]["summary"]).group()
            except:
                pass
            logger.debug("%s <- %s", match_ip, match_mac)
            if match_ip + match_mac in self.seenRing.get():
                continue
            else:
                self.seenRing.append(match_ip + match_mac)
            self.find_username_by_mac(match_mac, match_ip)

        logger.debug("Found %s DHCP events", len(events["hits"]))

    def find_username_by_mac(self, match_mac, match_ip):
        newmessage = {}
        newmessage["details"] = {}

        macobj = EUI(match_mac)
        try:
            oui = macobj.oui
            newmessage["details"]["hwvendor"] = oui.registration().org
        except NotRegisteredError as e:
            logger.debug("netaddr failed as usual - %s", e)
            pass
        macobj.dialect = mac_bare
        mac_bare_str = str(macobj)

        if match_mac[0:8].lower() in self.macassignments:
            newmessage["details"]["hwvendor"] = self.macassignments[
                match_mac[0:8].lower()
            ]
            logger.debug("found vendor in the out.txt")

        search_query = SearchQuery(hours=8)
        search_query.add_must(
            [
                TermMatch("category", "syslog"),
                TermMatch("facility", "local1"),
                QueryStringMatch("summary: " + mac_bare_str),
            ]
        )
        events = search_query.execute(self.esClient, indices=["events"])
        for event in events["hits"]:
            message = event["_source"]["summary"]
        logger.debug("Found %s Radius events", len(events["hits"]))

        if len(events["hits"]) == 0:
            return

        message_broken = message.split(",")

        message_dict = {}
        for f in message_broken:
            if "=" not in f:
                continue
            k, v = f.split("=")
            message_dict[k] = v
        del (message_broken)

        for key in self.yap["session"]:
            mappedvalue = jmespath.search(self.yap["session"][key], message_dict)
            if mappedvalue is not None:
                newmessage["details"][key] = mappedvalue
        del (message_dict)

        newmessage["details"]["macaddress"] = str(
            EUI(newmessage["details"]["macaddress"])
        )

        if newmessage["details"]["result"] == "REJECT":
            newmessage["details"]["success"] = False
        if newmessage["details"]["result"] == "ACCEPT":
            newmessage["details"]["success"] = True

        newmessage["details"]["eventipaddress"] = match_ip

        if len(events["hits"]) > 0:
            self.createevent(newmessage)

        return

    def getDocID(self, usermacaddress):
        # create a hash to use as the ES doc id // Thanks Jeff!!
        hash = md5()
        hash.update("{0}.mozdefintel.usernamemacaddress".format(usermacaddress))
        return hash.hexdigest()

    def createevent(self, newmessage):
        logger.debug("%s", newmessage)

        event = dict()
        event[u"utctimestamp"] = toUTC(
            newmessage["details"]["radiustimestamp"]
        ).isoformat()
        event[u"timestamp"] = toUTC(
            newmessage["details"]["radiustimestamp"]
        ).isoformat()
        event[u"receivedtimestamp"] = toUTC(datetime.now()).isoformat()
        event[u"mozdefhostname"] = self.hostname
        event[u"hostname"] = self.hostname
        event[u"processid"] = self.mypid
        event[u"processname"] = self.myname
        event[u"category"] = u"authentication"
        event[u"tags"] = [u"authentication", u"clearpass", u"dhcp"]
        event[u"source"] = u"clearpass"
        event[u"severity"] = u"INFO"
        event[u"details"] = newmessage["details"]

        logger.debug("%s", event)

        # XXX: doc_type="usernamemacaddress"
        # XXX: try to create index
        try:
            self.es.save_object(
                index="intelligence",
                doc_id=self.getDocID(event),
                doc_type="event",
                body=json.dumps(event),
            )
        except Exception as e:
            logger.error("Exception %r when posting correlation " % e)


def main():
    iptouser = UsernameNetResolve()
    iptouser.find_mac_by_ip()


if __name__ == "__main__":
    main()
