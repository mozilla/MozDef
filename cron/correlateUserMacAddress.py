#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# Copyright (c) 2014 Mozilla Corporation

import json
import re
import sys
from configlib import getConfig, OptionParser
from hashlib import md5

from mozdef_util.utilities.logger import logger
from mozdef_util.elasticsearch_client import ElasticsearchClient, ElasticsearchBadServer
from mozdef_util.query_models import SearchQuery, TermMatch, PhraseMatch


def getDocID(usermacaddress):
    # create a hash to use as the ES doc id
    hash = md5()
    seed = '{0}.mozdefintel.usernamemacaddress'.format(usermacaddress)
    hash.update(seed.encode())
    return hash.hexdigest()


def readOUIFile(ouifilename):
    '''
    Expects the OUI file from IEEE:
    wget http://www.ieee.org/netstorage/standards/oui.txt
    Reads the (hex) line and extracts the hex prefix and the vendor name
    to store as part of the intelligence record about what device the user
    was seen using.
    '''
    ouifile=open(ouifilename)
    macassignments={}
    for i in ouifile.readlines()[0::]:
        i=i.strip()
        if '(hex)' in i:
            # print(i)
            fields=i.split('\t')
            macprefix=fields[0][0:8].replace('-',':').lower()
            entity=fields[2]
            macassignments[macprefix]=entity
    return macassignments


def esSearch(es, macassignments=None):
    '''
    Search ES for an event that ties a username to a mac address
    This example searches for junos wifi correlations on authentication success
    Expecting an event like: user: username@somewhere.com; mac: 5c:f9:38:b1:de:cf; author reason: roamed session; ssid: ANSSID; AP 46/2\n
    '''
    usermacre=re.compile(r'''user: (?P<username>.*?); mac: (?P<macaddress>.*?); ''',re.IGNORECASE)
    correlations={}

    search_query = SearchQuery(minutes=options.correlationminutes)
    search_query.add_must(TermMatch('details.program', 'AUTHORIZATION-SUCCESS'))
    search_query.add_must_not(PhraseMatch('summary', 'last-resort'))

    try:
        full_results = search_query.execute(es)
        results = full_results['hits']

        for r in results:
            fields = re.search(usermacre,r['_source']['summary'])
            if fields:
                if '{0} {1}'.format(fields.group('username'),fields.group('macaddress')) not in correlations:
                    if fields.group('macaddress')[0:8].lower() in macassignments:
                        entity=macassignments[fields.group('macaddress')[0:8].lower()]
                    else:
                        entity='unknown'
                    correlations['{0} {1}'.format(fields.group('username'),fields.group('macaddress'))]=dict(username=fields.group('username'),
                                                                                                             macaddress=fields.group('macaddress'),
                                                                                                             entity=entity,
                                                                                                             utctimestamp=r['_source']['utctimestamp'])
        return correlations

    except ElasticsearchBadServer:
        logger.error('Elastic Search server could not be reached, check network connectivity')


def esStoreCorrelations(es, correlations):
    for c in correlations:
        event=dict(
            utctimestamp=correlations[c]['utctimestamp'],
            summary=c,
            details=dict(
                username=correlations[c]['username'],
                macaddress=correlations[c]['macaddress'],
                entity=correlations[c]['entity']
            ),
            category='indicators'
        )
        try:
            es.save_object(index='intelligence', doc_id=getDocID(c), body=json.dumps(event))
        except Exception as e:
            logger.error("Exception %r when posting correlation " % e)


def main():
    '''
    Look for events that contain username and a mac address
    Add the correlation to the intelligence index.
    '''
    logger.debug('starting')
    logger.debug(options)

    es = ElasticsearchClient((list('{0}'.format(s) for s in options.esservers)))
    # create intelligence index if it's not already there
    es.create_index('intelligence')

    # read in the OUI file for mac prefix to vendor dictionary
    macassignments = readOUIFile(options.ouifilename)

    # search ES for events containing username and mac address
    correlations = esSearch(es, macassignments=macassignments)

    # store the correlation in the intelligence index
    esStoreCorrelations(es, correlations)

    logger.debug('finished')


def initConfig():
    # output our log to stdout or syslog
    options.output = getConfig('output', 'stdout', options.configfile)
    # syslog hostname
    options.sysloghostname = getConfig('sysloghostname',
                                       'localhost',
                                       options.configfile)
    # syslog port
    options.syslogport = getConfig('syslogport', 514, options.configfile)

    # elastic search server settings
    options.esservers = list(getConfig('esservers',
                                       'http://localhost:9200',
                                       options.configfile).split(','))

    # default time period in minutes to look back in time for the aggregation
    options.correlationminutes = getConfig('correlationminutes',
                                           150,
                                           options.configfile)

    # default location of the OUI file from IEEE for resolving mac prefixes
    # Expects the OUI file from IEEE:
    # wget http://www.ieee.org/netstorage/standards/oui.txt
    options.ouifilename = getConfig('ouifilename',
                                    'oui.txt',
                                    options.configfile)


if __name__ == '__main__':
    parser = OptionParser()
    parser.add_option(
        "-c",
        dest='configfile',
        default=sys.argv[0].replace('.py', '.conf'),
        help="configuration file to use")
    (options, args) = parser.parse_args()
    initConfig()
    main()
