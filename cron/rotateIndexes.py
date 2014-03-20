#!/usr/bin/env python
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import sys
import pyes
from datetime import datetime
from datetime import date
from configlib import getConfig,OptionParser

def esRotateIndexes():
    es=pyes.ES((list('{0}'.format(s) for s in options.esservers)))
    
    indexes=es.indices.stats()['indices'].keys()
    #print('[*]\tcurrent indexes: {0}'.format(indexes))
    
    #set index names events-MMYYDD, etc.
    dtNow=datetime.utcnow()
    indexSuffix=date.strftime(dtNow,'%Y%m%d')
    eventsIndexName='events-{0}'.format(indexSuffix)
    alertsIndexName='alerts-{0}'.format(indexSuffix)
    correlationsIndexName='correlations-{0}'.format(indexSuffix)
    print('[*]\tlooking for current daily indexes: {0},{1},{2}'.format(eventsIndexName,alertsIndexName,correlationsIndexName))
    
    if eventsIndexName not in indexes:
        print('[*]\tcreating: {0}'.format(eventsIndexName))
        #es.create_index(eventsIndexName)
        es.indices.create_index(eventsIndexName)
    if alertsIndexName not in indexes:
        print('[*]\tcreating: {0}'.format(alertsIndexName))
        #es.create_index(alertsIndexName)
        es.indices.create_index(alertsIndexName)
    if correlationsIndexName not in indexes:
        print('[*]\tcreating: {0}'.format(correlationsIndexName))
        #es.create_index(correlationsIndexName)
        es.indices.create_index(correlationsIndexName)
    
    print('[*]\tensuring aliases are current')
    es.indices.set_alias('events', eventsIndexName)
    es.indices.set_alias('alerts', alertsIndexName)
    es.indices.set_alias('correlations', correlationsIndexName)
    
def initConfig():
    options.esservers=list(getConfig('esservers','http://localhost:9200',options.configfile).split(','))
    
if __name__ == '__main__':
    parser=OptionParser()
    parser.add_option("-c", dest='configfile' , default='{0}.conf'.format(sys.argv[0]), help="configuration file to use")
    (options,args) = parser.parse_args()
    initConfig()
    esRotateIndexes()
