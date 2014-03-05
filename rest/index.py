# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import sys
import bottle
from bottle import debug,route, run, template, response,request,post, default_app
from bottle import _stdout as bottlelog
import json
from configlib import getConfig,OptionParser
import pyes
from elasticutils import S
from datetime import datetime
from datetime import timedelta
from dateutil.parser import parse
import pytz

options=None
# cors decorator for rest/ajax
def enable_cors(fn):
    def _enable_cors(*args, **kwargs):
        # set CORS headers
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Origin, Accept, Content-Type, X-Requested-With, X-CSRF-Token'

        if bottle.request.method != 'OPTIONS':
            # actual request; reply with the actual response
            return fn(*args, **kwargs)

    return _enable_cors

@route('/test')
@route('/test/')
def index():
    ip = request.environ.get('REMOTE_ADDR')
    #response.headers['X-IP'] = '{0}'.format(ip)
    response.status=200

@route('/status')
@route('/status/')
def index():
    if request.body:
        request.body.read()
        request.body.close()
    response.status=200
    response.content_type="application/json"
    return(json.dumps(dict(status='ok')))

@route('/ldapLogins')
@route('/ldapLogins/')
@enable_cors
def index():
    if request.body:
        request.body.read()
        request.body.close()
    response.content_type="application/json"
    return(esLdapResults())    


@route('/alerts')
@route('/alerts/')
@enable_cors
def index():
    if request.body:
        request.body.read()
        request.body.close()
    response.content_type="application/json"
    return(esAlertsSummary())   
    
#debug(True)
def toUTC(suspectedDate,localTimeZone="US/Pacific"):
    '''make a UTC date out of almost anything'''
    utc=pytz.UTC
    objDate=None
    if type(suspectedDate)==str:
        objDate=parse(suspectedDate,fuzzy=True)
    elif type(suspectedDate)==datetime:
        objDate=suspectedDate
    
    if objDate.tzinfo is None:
        objDate=pytz.timezone(localTimeZone).localize(objDate)
        objDate=utc.normalize(objDate)
    else:
        objDate=utc.normalize(objDate)
    if objDate is not None:
        objDate=utc.normalize(objDate)
        
    return objDate

def esAlertsSummary(begindateUTC=None, enddateUTC=None):
    resultsList=list()
    if begindateUTC is None:
        begindateUTC=datetime.now() - timedelta(hours=12)
        begindateUTC=toUTC(begindateUTC)
    if enddateUTC is None:
        enddateUTC= datetime.now()
        enddateUTC= toUTC(enddateUTC)
    try:

        #q=S().es(urls=['http://{0}:{1}'.format(options.esserver,options.esport)]).query(_type='alert').filter(utctimestamp__range=[begindateUTC.isoformat(),enddateUTC.isoformat()])
        #f=q.facet_raw(alerttype={"terms" : {"script_field" : "_source.type","size" : 500}})
        
        #get all alerts
        q= S().es(urls=['http://{0}:{1}'.format(options.esserver,options.esport)]).query(_type='alert')
        #create a facet field using the entire 'type' field  (not the sub terms) and filter it by date. 
        f=q.facet_raw(\
            alerttype={"terms" : {"script_field" : "_source.category"},\
            "facet_filter":{'range': {'utctimestamp': \
                                     {'gte': begindateUTC.isoformat(), 'lte': enddateUTC.isoformat()}}}\

            })        
        return(json.dumps(f.facet_counts()['alerttype']))
                
    except Exception as e :
        sys.stderr.write('%r'%e)
        
def esLdapResults(begindateUTC=None, enddateUTC=None):
    resultsList=list()
    if begindateUTC is None:
        begindateUTC=datetime.now() - timedelta(hours=12)
        begindateUTC=toUTC(begindateUTC)
    if enddateUTC is None:
        enddateUTC= datetime.now()
        enddateUTC= toUTC(enddateUTC)
    try:
        es=pyes.ES(("http",options.esserver,options.esport))
        #qDate=e=pyes.MatchQuery("message",options.datePhrase,"phrase")
        qDate=pyes.RangeQuery(qrange=pyes.ESRange('utctimestamp',from_value=begindateUTC,to_value=enddateUTC))
        q = pyes.MatchAllQuery()
        q = pyes.FilteredQuery(q,qDate)
        q = pyes.FilteredQuery(q,pyes.TermFilter('tags','ldap'))
        q = pyes.FilteredQuery(q,pyes.TermFilter('details.result','ldap_invalid_credentials'))
        q2=q.search()
        q2.facet.add_term_facet('details.result')
        q2.facet.add_term_facet('details.dn',size=20)
        results=es.search(q2)
        #sys.stdout.write('{0}\n'.format(results.facets))
    
        stoplist=('o','mozilla','dc','com','mozilla.com','mozillafoundation.org','org')
        for t in results.facets['details.dn'].terms:
            if t['term'] in stoplist:
                continue
            #print(t['term'])
            failures=0
            success=0
            dn=t['term']

            #re-query with the terms of the details.dn
            qt = pyes.MatchAllQuery()
            qt = pyes.FilteredQuery(qt,qDate)
            qt = pyes.FilteredQuery(qt,pyes.TermFilter('tags','ldap'))
            qt = pyes.FilteredQuery(qt,pyes.TermFilter('details.dn',t['term']))
            qt2=qt.search()
            qt2.facet.add_term_facet('details.result')
            results=es.search(qt2)
            #sys.stdout.write('{0}\n'.format(results.facets['details.result'].terms))
            
            for t in results.facets['details.result'].terms:
                #print(t['term'],t['count'])
                if t['term']=='ldap_success':
                    success=t['count']
                if t['term']=='ldap_invalid_credentials':
                    failures=t['count']
            resultsList.append(dict(dn=dn,failures=failures,success=success,begin=begindateUTC.isoformat(),end=enddateUTC.isoformat()))
        
        return(json.dumps(resultsList))
    except pyes.exceptions.NoServerAvailable:
        sys.stderr.write('Elastic Search server could not be reached, check network connectivity\n')
     
        
def initConfig():
    #change this to your default zone for when it's not specified
    options.defaultTimeZone=getConfig('defaulttimezone','US/Pacific',options.configfile)
    options.esserver=getConfig('esserver','localhost',options.configfile)
    options.esport=getConfig('esport',9200,options.configfile)
    
if __name__ == "__main__":
    parser=OptionParser()
    parser.add_option("-c", dest='configfile' , default='index.conf', help="configuration file to use")
    (options,args) = parser.parse_args()
    initConfig()
    run(host="localhost", port=8081)
else:
    parser=OptionParser()
    parser.add_option("-c", dest='configfile' , default='index.conf', help="configuration file to use")
    (options,args) = parser.parse_args()
    initConfig()    
    application = default_app()
