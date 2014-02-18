#!/usr/bin/env python
import pyes
from optparse import OptionParser
from datetime import datetime
from datetime import date

def esRotateIndexes():
    es=pyes.ES(("http",options.server,options.port))
    
    #indexes=es.status()['indices'].keys()
    indexes=es.indices.stats()['indices'].keys()
    print('[*]\tcurrent indexes: {0}'.format(indexes))
    
    #set index names events-MMYYDD, etc.
    dtNow=datetime.now()
    indexSuffix=date.strftime(dtNow,'%Y%m%d')
    eventsIndexName='events-{0}'.format(indexSuffix)
    alertsIndexName='alerts-{0}'.format(indexSuffix)
    correlationsIndexName='correlations-{0}'.format(indexSuffix)
    print('[*]\tlooking for current daily indexes: {0},{1},{2}'.format(eventsIndexName,alertsIndexName,correlationsIndexName))
    
    if eventsIndexName not in indexes:
        print('[-]\tcreating: {0}'.format(eventsIndexName))
        #es.create_index(eventsIndexName)
        es.indices.create_index(eventsIndexName)
    if alertsIndexName not in indexes:
        print('[-]\tcreating: {0}'.format(alertsIndexName))
        #es.create_index(alertsIndexName)
        es.indices.create_index(alertsIndexName)
    if correlationsIndexName not in indexes:
        print('[-]\tcreating: {0}'.format(correlationsIndexName))
        #es.create_index(correlationsIndexName)
        es.indices.create_index(correlationsIndexName)
    
    print('[*]\tensuring aliases are current')
    es.indices.set_alias('events', eventsIndexName)
    es.indices.set_alias('alerts', alertsIndexName)
    es.indices.set_alias('correlations', correlationsIndexName)
    
    
    
        
if __name__ == '__main__':
    parser=OptionParser()
    parser=OptionParser()
    parser.add_option("-s", "--server", dest='server' , default='localhost', help="elastic search servername or ip address")
    parser.add_option("-p", "--port", dest='port', default=9200, type="int", help="elastic search port")
    (options,args) = parser.parse_args()

    esRotateIndexes()
