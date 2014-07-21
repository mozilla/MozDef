# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
# Copyright (c) 2014 Mozilla Corporation
#
# Contributors:
# Jeff Bryner jbryner@mozilla.com
# Anthony Verez averez@mozilla.com

import bottle
import json
import MySQLdb
import netaddr
import pyes
import pytz
import requests
import sys
from bottle import debug, route, run, response, request, default_app, post
from datetime import datetime, timedelta
from configlib import getConfig, OptionParser
from elasticutils import S
from datetime import datetime
from datetime import timedelta
from dateutil.parser import parse
from ipwhois import IPWhois

options = None
dbcursor = None
mysqlconn = None


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
    # response.headers['X-IP'] = '{0}'.format(ip)
    response.status = 200


@route('/status')
@route('/status/')
def index():
    if request.body:
        request.body.read()
        request.body.close()
    response.status = 200
    response.content_type = "application/json"
    return(json.dumps(dict(status='ok')))


@route('/ldapLogins')
@route('/ldapLogins/')
@enable_cors
def index():
    if request.body:
        request.body.read()
        request.body.close()
    response.content_type = "application/json"
    return(esLdapResults())


@route('/alerts')
@route('/alerts/')
@enable_cors
def index():
    if request.body:
        request.body.read()
        request.body.close()
    response.content_type = "application/json"
    return(esAlertsSummary())


@route('/kibanadashboards')
@route('/kibanadashboards/')
@enable_cors
def index():
    if request.body:
        request.body.read()
        request.body.close()
    response.content_type = "application/json"
    return(kibanaDashboards())


@post('/blockip', methods=['POST'])
@post('/blockip/', methods=['POST'])
@enable_cors
def index():
    if options.enableBlockIP:
        try:
            return(banhammer(request.json))
        except Exception as e:
            sys.stderr.write('Error parsing json sent to POST /banhammer\n')


@post('/ipwhois', methods=['POST'])
@post('/ipwhois/', methods=['POST'])
@enable_cors
def index():
    '''return a json version of whois for an ip address'''
    if request.body:
        arequest = request.body.read()
        request.body.close()
    # valid json?
    try:
        requestDict = json.loads(arequest)
    except ValueError as e:
        response.status = 500
        return        
    if 'ipaddress' in requestDict.keys() and isIPv4(requestDict['ipaddress']):
        response.content_type = "application/json"
        return(getWhois(requestDict['ipaddress']))
    else:
        response.status = 500
        return

@post('/ipcifquery', methods=['POST'])
@post('/ipcifquery/', methods=['POST'])
@enable_cors
def index():
    '''return a json version of cif query for an ip address'''
    if request.body:
        arequest = request.body.read()
        request.body.close()
    # valid json?
    try:
        requestDict = json.loads(arequest)
    except ValueError as e:
        response.status = 500
        return        
    if 'ipaddress' in requestDict.keys() and isIPv4(requestDict['ipaddress']):
        response.content_type = "application/json"
        return(getIPCIF(requestDict['ipaddress']))
    else:
        response.status = 500
        return    

@post('/ipdshieldquery', methods=['POST'])
@post('/ipdshieldquery/', methods=['POST'])
@enable_cors
def index():
    '''
    return a json version of dshield query for an ip address
    https://isc.sans.edu/api/index.html
    '''
    if request.body:
        arequest = request.body.read()
        request.body.close()
    # valid json?
    try:
        requestDict = json.loads(arequest)
    except ValueError as e:
        response.status = 500
        return        
    if 'ipaddress' in requestDict.keys() and isIPv4(requestDict['ipaddress']):
        url="https://isc.sans.edu/api/ip/"
        
        dresponse = requests.get('{0}{1}?json'.format(url, requestDict['ipaddress']))
        if dresponse.status_code == 200:
            response.content_type = "application/json"
            return(dresponse.content)
        else:
            response.status = dresponse.status_code
            return
    else:
        response.status = 500
        return


def toUTC(suspectedDate, localTimeZone="US/Pacific"):
    '''make a UTC date out of almost anything'''
    utc = pytz.UTC
    objDate = None
    if type(suspectedDate) == str:
        objDate = parse(suspectedDate, fuzzy=True)
    elif type(suspectedDate) == datetime:
        objDate = suspectedDate

    if objDate.tzinfo is None:
        objDate = pytz.timezone(localTimeZone).localize(objDate)
        objDate = utc.normalize(objDate)
    else:
        objDate = utc.normalize(objDate)
    if objDate is not None:
        objDate = utc.normalize(objDate)

    return objDate


def isIPv4(ip):
    try:
        # netaddr on it's own considers 1 and 0 to be valid_ipv4
        # so a little sanity check prior to netaddr.
        # Use IPNetwork instead of valid_ipv4 to allow CIDR
        if '.' in ip and len(ip.split('.')) == 4:
            # some ips are quoted
            netaddr.IPNetwork(ip.strip("'").strip('"'))
            return True
        else:
            return False
    except:
        return False


def esAlertsSummary(begindateUTC=None, enddateUTC=None):
    resultsList = list()
    if begindateUTC is None:
        begindateUTC = datetime.now() - timedelta(hours=12)
        begindateUTC = toUTC(begindateUTC)
    if enddateUTC is None:
        enddateUTC = datetime.now()
        enddateUTC = toUTC(enddateUTC)
    try:

        #q=S().es(urls=['http://{0}:{1}'.format(options.esserver,options.esport)]).query(_type='alert').filter(utctimestamp__range=[begindateUTC.isoformat(),enddateUTC.isoformat()])
        #f=q.facet_raw(alerttype={"terms" : {"script_field" : "_source.type","size" : 500}})

        #get all alerts
        #q= S().es(urls=['http://{0}:{1}'.format(options.esserver,options.esport)]).query(_type='alert')
        q= S().es(urls=list('{0}'.format(s) for s in options.esservers)).query(_type='alert')
        #create a facet field using the entire 'category' field  (not the sub terms) and filter it by date. 
        f=q.facet_raw(\
            alerttype={"terms" : {"script_field" : "_source.category"},\
            "facet_filter":{'range': {'utctimestamp': \
                                     {'gte': begindateUTC.isoformat(), 'lte': enddateUTC.isoformat()}}}\

            })
        return(json.dumps(f.facet_counts()['alerttype']))

    except Exception as e:
        sys.stderr.write('%r' % e)


def esLdapResults(begindateUTC=None, enddateUTC=None):
    resultsList = list()
    if begindateUTC is None:
        begindateUTC = datetime.now() - timedelta(hours=12)
        begindateUTC = toUTC(begindateUTC)
    if enddateUTC is None:
        enddateUTC = datetime.now()
        enddateUTC = toUTC(enddateUTC)
    try:
        es = pyes.ES((list('{0}'.format(s) for s in options.esservers)))
        qDate = pyes.RangeQuery(qrange=pyes.ESRange('utctimestamp',
            from_value=begindateUTC, to_value=enddateUTC))
        q = pyes.MatchAllQuery()
        q = pyes.FilteredQuery(q, qDate)
        q = pyes.FilteredQuery(q, pyes.TermFilter('tags', 'ldap'))
        q = pyes.FilteredQuery(q,
            pyes.TermFilter('details.result', 'ldap_invalid_credentials'))
        q2 = q.search()
        q2.facet.add_term_facet('details.result')
        q2.facet.add_term_facet('details.dn', size=20)
        results = es.search(q2, indices='events')

        stoplist = ('o', 'mozilla', 'dc', 'com', 'mozilla.com',
            'mozillafoundation.org', 'org')
        for t in results.facets['details.dn'].terms:
            if t['term'] in stoplist:
                continue
            #print(t['term'])
            failures = 0
            success = 0
            dn = t['term']

            #re-query with the terms of the details.dn
            qt = pyes.MatchAllQuery()
            qt = pyes.FilteredQuery(qt, qDate)
            qt = pyes.FilteredQuery(qt, pyes.TermFilter('tags', 'ldap'))
            qt = pyes.FilteredQuery(qt,
                pyes.TermFilter('details.dn', t['term']))
            qt2 = qt.search()
            qt2.facet.add_term_facet('details.result')
            results = es.search(qt2)
            #sys.stdout.write('{0}\n'.format(results.facets['details.result'].terms))

            for t in results.facets['details.result'].terms:
                #print(t['term'],t['count'])
                if t['term'] == 'ldap_success':
                    success = t['count']
                if t['term'] == 'ldap_invalid_credentials':
                    failures = t['count']
            resultsList.append(dict(dn=dn, failures=failures,
                success=success, begin=begindateUTC.isoformat(),
                end=enddateUTC.isoformat()))

        return(json.dumps(resultsList))
    except pyes.exceptions.NoServerAvailable:
        sys.stderr.write('Elastic Search server could not be reached, check network connectivity\n')


def kibanaDashboards():
    try:
        resultsList = []
        es = pyes.ES((list('{0}'.format(s) for s in options.esservers)))
        r = es.search(pyes.Search(pyes.MatchAllQuery(), size=100),
            'kibana-int', 'dashboard')
        if r:
            for dashboard in r:
                dashboardJson = json.loads(dashboard.dashboard)
                resultsList.append({
                    'name': dashboardJson['title'],
                    'url': "%s/%s/%s" % (options.kibanaurl,
                        "index.html#/dashboard/elasticsearch",
                        dashboardJson['title'])
                })
            return json.dumps(resultsList)
        else:
            sys.stderr.write('No Kibana dashboard found\n')
    except pyes.exceptions.NoServerAvailable:
        sys.stderr.write('Elastic Search server could not be reached, check network connectivity\n')


def banhammer(action):
    try:
        mysqlconn = MySQLdb.connect(
            host=options.banhammerdbhost,
            user=options.banhammerdbuser,
            passwd=options.banhammerdbpasswd,
            db=options.banhammerdbdb)
        dbcursor = mysqlconn.cursor()
        # Look if attacker already in the DB, if yes get id
        dbcursor.execute("""SELECT id FROM blacklist_offender
              WHERE address = "%s" AND cidr = %d""" % (action['address'], int(action['cidr'])))
        qresult = dbcursor.fetchone()
        if not qresult:
            # insert new attacker in banhammer DB
            created_date = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
            dbcursor.execute("""
                INSERT INTO blacklist_offender(address, cidr)
                VALUES ("%s", %d)
            """ % (action['address'], action['cidr']))
            # get the ID of this query
            dbcursor.execute("""SELECT id FROM blacklist_offender
              WHERE address = "%s" AND cidr = %d""" % (action['address'], int(action['cidr'])))
            qresult = dbcursor.fetchone()
        (attacker_id,) = qresult
        # Compute start and end dates
        start_date = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        end_date = datetime.utcnow() + timedelta(hours=1)
        if action['duration'] == '12hr':
            end_date = datetime.utcnow() + timedelta(hours=12)
        elif action['duration'] == '1d':
            end_date = datetime.utcnow() + timedelta(days=1)
        elif action['duration'] == '1w':
            end_date = datetime.utcnow() + timedelta(days=7)
        elif action['duration'] == '30d':
            end_date = datetime.utcnow() + timedelta(days=30)

        if action['bugid']:
            # Insert in DB
            dbcursor.execute("""
                INSERT INTO blacklist_blacklist(offender_id, start_date, end_date, comment, reporter, bug_number)
                VALUES (%d, "%s", "%s", "%s", "%s", %d)
                """ % (attacker_id, start_date, end_date, action['comment'], action['reporter'], int(action['bugid'])))
        else:
            dbcursor.execute("""
                INSERT INTO blacklist_blacklist(offender_id, start_date, end_date, comment, reporter)
                VALUES (%d, "%s", "%s", "%s", "%s")
                """ % (attacker_id, start_date, end_date, action['comment'], action['reporter']))
        mysqlconn.commit()
        sys.stderr.write('%s/%d: banhammered\n' % (action['address'], action['cidr']))
    except Exception as e:
        sys.stderr.write('Error while banhammering %s/%d: %s\n' % (action['address'], action['cidr'], e))


def getWhois(ipaddress):
    try:
        whois = IPWhois(netaddr.IPNetwork(ipaddress)[0]).lookup()
        return (json.dumps(whois))
    except Exception as e:
        sys.stderr.write('Error looking up whois for {0}: {1}\n'.format(ipaddress, e))

def getIPCIF(ipaddress):
    # query a CIF service for information on this IP address per:
    # https://code.google.com/p/collective-intelligence-framework/wiki/API_HTTP_v1
    try:
        resultsList = []
        url='{0}api?apikey={1}&limit=20&confidence=65&q={2}'.format(options.cifhosturl,
                                             options.cifapikey,
                                             ipaddress)
        headers = {'Accept': 'application/json'}
        r=requests.get(url=url,verify=False,headers=headers)
        if r.status_code == 200:
            # we get a \n delimited list of json entries
            cifjsons=r.text.split('\n')
            for c in cifjsons:
                # test for valid json
                try:
                    resultsList.append(json.loads(c))
                except ValueError:
                    pass
            return json.dumps(resultsList)

    except Exception as e:
        sys.stderr.write('Error looking up CIF results for {0}: {1}\n'.format(ipaddress, e))

        
def checkBlockIPService():
    if options.enableBlockIP:
        try:
            mysqlconn = MySQLdb.connect(
                host=options.banhammerdbhost,
                user=options.banhammerdbuser,
                passwd=options.banhammerdbpasswd,
                db=options.banhammerdbdb)
            dbcursor = mysqlconn.cursor()
        except Exception as e:
            sys.stderr.write('Failed to connect to the Banhammer DB\n')    


def initConfig():
    #change this to your default zone for when it's not specified
    options.defaultTimeZone = getConfig('defaulttimezone',
                                        'US/Pacific',
                                        options.configfile)
    options.esservers = list(getConfig('esservers',
                                       'http://localhost:9200',
                                       options.configfile).split(','))
    options.kibanaurl = getConfig('kibanaurl',
                                  'http://localhost:9090',
                                  options.configfile)
    
    # options for your custom/internal ip blocking service
    # mozilla's is called banhammer
    # and uses an intermediary mysql DB
    # here we set credentials
    options.enableBlockIP = getConfig('enableBlockIP',
                                      False,
                                      options.configfile)
    options.banhammerdbhost = getConfig('banhammerdbhost',
                                        'localhost',
                                        options.configfile)
    options.banhammerdbuser = getConfig('banhammerdbuser',
                                        'auser',
                                        options.configfile)
    options.banhammerdbpasswd = getConfig('banhammerdbpasswd',
                                          '',
                                          options.configfile)
    options.banhammerdbdb = getConfig('banhammerdbdb',
                                      'banhammer',
                                      options.configfile)
    
    # options for your CIF service
    options.cifapikey = getConfig('cifapikey', '', options.configfile)
    options.cifhosturl = getConfig('cifhosturl',
                                   'http://localhost/',
                                   options.configfile)


    # check any service you'd like at startup rather than waiting
    # for a client request.
    checkBlockIPService()


if __name__ == "__main__":
    parser = OptionParser()
    parser.add_option("-c", dest='configfile',
        default=sys.argv[0].replace('.py', '.conf'),
        help="configuration file to use")
    (options, args) = parser.parse_args()
    initConfig()

    run(host="localhost", port=8081)
else:
    parser = OptionParser()
    parser.add_option("-c", dest='configfile',
        default=sys.argv[0].replace('.py', '.conf'),
        help="configuration file to use")
    (options, args) = parser.parse_args()
    initConfig()

    application = default_app()
