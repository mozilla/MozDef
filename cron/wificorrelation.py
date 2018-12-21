import os
import sys
import jmespath
import logging
import mozdef_client as mozdef
from yaml import load
from re import compile
from mozdef_util.utilities.toUTC import toUTC
from netaddr import EUI, mac_bare, NotRegisteredError
from datetime import datetime, timedelta, tzinfo
from mozdef_util.elasticsearch_client import ElasticsearchClient
from mozdef_util.query_models import TermMatch, SearchQuery, RangeMatch, QueryStringMatch
from configlib import getConfig, OptionParser
from logging.handlers import SysLogHandler

class UsernameNetResolve:

    def __init__(self):
        self.logger = logging.getLogger(sys.argv[0])
        self.initParser()
        self.initConfig()
        self.initLogger()
        self.initYap()
        self.macassignments = self.readOUIFile()
        self.esClient = ElasticsearchClient(self.options.esreadurl)
        self.logger.debug('started')

    def loggerTimeStamp(self, record, datefmt=None):
        return toUTC(datetime.now()).isoformat()

    def initLogger(self):
        self.logger.level = logging.DEBUG
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        formatter.formatTime = self.loggerTimeStamp
        if self.options.output == 'syslog':
            self.logger.addHandler(
                SysLogHandler(address=(self.options.sysloghostname,
                                       self.options.syslogport)))
        else:
            sh = logging.StreamHandler(sys.stderr)
            sh.setFormatter(formatter)
            self.logger.addHandler(sh)

    def initConfig(self):
        self.options.output= getConfig('output', 'stdout', self.options.configfile)
        self.options.esreadurl= getConfig('esreadurl', 'localhost:9200', self.options.configfile)
        self.options.eswriteurl= getConfig('eswriteurl', 'localhost:9200', self.options.configfile)
        self.options.cpmap= getConfig('cpmap', '<empty>', self.options.configfile)
        self.options.dhcpexclude= getConfig('dhcpexclude', '<empty>', self.options.configfile)

    def initParser(self):
        parser = OptionParser()
        parser.add_option(
            "-c",
            dest='configfile',
            default=sys.argv[0].replace('.py', '.conf'),
            help="configuration file to use")
        (self.options, args) = parser.parse_args()

    def initYap(self):
        with open(os.path.join(os.path.dirname(__file__), self.options.cpmap), 'r') as f:
            map = f.read()

        yap = load(map)
        eventtypes = yap.keys()
        del(map)

    def readOUIFile(self):
        '''
        Expects the OUI file from IEEE:
        wget http://www.ieee.org/netstorage/standards/oui.txt
        Reads the (hex) line and extracts the hex prefix and the vendor name
        to store as part of the intelligence record about what device the user
        was seen using.
        '''
        ouifilename='oui.txt'
        # ugly, change to with, catch exception, print exception, test that
        with open(ouifilename) as ouifile:
            macassignments={}
            for i in ouifile.readlines()[0::]:
                i=i.strip()
                if '(hex)' in i:
                    fields=i.split('\t')
                    macprefix=fields[0][0:8].replace('-',':').lower()
                    entity=fields[2]
                    macassignments[macprefix]=entity
        self.logger.debug('The MAC OUI database loaded - %s entries', len(macassignments))
        return macassignments

    def find_mac_by_ip(self):
        ip = compile('(([2][5][0-5]\.)|([2][0-4][0-9]\.)|([0-1]?[0-9]?[0-9]\.)){3}'
                    +'(([2][5][0-5])|([2][0-4][0-9])|([0-1]?[0-9]?[0-9]))')
        mac = compile('([a-fA-F0-9]{2}[:|\-]?){6}')

        search_query = SearchQuery(seconds=60)
        search_query.add_must([
            TermMatch('category', 'syslog'),
            TermMatch('processname', 'dhcpd'),
            QueryStringMatch('summary: DHCPOFFER')
        ])
        for de in self.options.dhcpexclude.split(' '):
            search_query.add_must_not([
                TermMatch('hostname', de)
            ])
        events = search_query.execute(self.esClient, indices=['events-weekly'])

        for event in events['hits']:
            try:
                match_ip = ip.search(event['_source']['summary']).group()
            except:
                pass
            try:
                match_mac = mac.search(event['_source']['summary']).group()
            except:
                pass
            self.logger.debug('%s <- %s', match_ip, match_mac)
            self.find_username_by_mac(match_mac, match_ip)

        self.logger.debug('Found %s DHCP events',len(events['hits']))

    def find_username_by_mac(self, match_mac, match_ip):
        newmessage = {}
        newmessage['details'] = {}

        macobj = EUI(match_mac)
        try:
            oui = macobj.oui
            newmessage['details']['hwvendor'] = oui.registration().org
        except NotRegisteredError as e:
            self.logger.debug('netaddr failed as usual - %s', e)
            pass
        macobj.dialect = mac_bare
        mac_bare_str = str(macobj)

        if match_mac[0:8].lower() in self.macassignments:
            newmessage['details']['hwvendor'] = self.macassignments[match_mac[0:8].lower()]
            self.logger.debug('found vendor in the out.txt')

        search_query = SearchQuery(seconds=90)
        search_query.add_must([
            TermMatch('category', 'syslog'),
            TermMatch('facility', 'local1'),
            QueryStringMatch('summary: '+mac_bare_str)
        ])
        events = search_query.execute(self.esClient, indices=['events-weekly'])
        for event in events['hits']:
            message = event['_source']['summary']
        self.logger.debug('Found %s Radius events',len(events['hits']))

        if len(events['hits']) == 0:
            return

        message_broken = message.split(',')

        message_dict = {}
        for f in message_broken:
            if '=' not in f:
                continue
            k, v = f.split('=')
            message_dict[k] = v
        del(message_broken)

        for key in self.yap['session']:
            mappedvalue = jmespath.search(self.yap['session'][key], message_dict)
            if mappedvalue is not None:
                newmessage['details'][key] = mappedvalue
        del(message_dict)

        newmessage['details']['macaddress'] = str(EUI(newmessage['details']['macaddress']))

        if newmessage['details']['result'] == 'REJECT':
            newmessage['details']['success'] = False
        if newmessage['details']['result'] == 'ACCEPT':
            newmessage['details']['success'] = True

        newmessage['details']['eventipaddress'] = match_ip

        if len(events['hits']) > 0:
            self.createevent(newmessage)
 
        return

    def createevent(self, newmessage):
        self.logger.debug('%s', newmessage)

        mozmsg = mozdef.MozDefEvent(self.options.eswriteurl)
        mozmsg.tags = ['authentication', 'clearpass', 'dhcp']
        mozmsg.set_category('authentication')
        #if options.DEBUG:
        #    mozmsg.debug = options.DEBUG
        #    mozmsg.set_send_to_syslog(True, only_syslog=True)

        mozmsg.timestamp = toUTC(newmessage['details']['radiustimestamp']).isoformat()

        mozmsg.details = newmessage['details']
        mozmsg.summary = '%s <- %s'.format(newmessage['details']['username'], newmessage['details']['ipaddress'])

        mozmsg.send()

def main():
    iptouser = UsernameNetResolve()
    iptouser.find_mac_by_ip()

if __name__ == '__main__':
    main()
