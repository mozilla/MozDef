# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
# Copyright (c) 2014 Mozilla Corporation
#
# Contributors:
# Jeff Bryner jbryner@mozilla.com
# Anthony Verez averez@mozilla.com

import sys
import bottle
from bottle import debug,route, run, response, request, default_app, post
import json
from configlib import getConfig, OptionParser
import pyes
from elasticutils import S
from datetime import datetime
from datetime import timedelta
from dateutil.parser import parse
import pytz
import MySQLdb
from datetime import datetime, timedelta

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
    #response.headers['X-IP'] = '{0}'.format(ip)
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


@post('/banhammer', methods=['POST'])
@post('/banhammer/', methods=['POST'])
@enable_cors
def index():
    if (options.banhammerenable == 'true'):
        try:
            return(banhammer(request.json))
        except Exception as e:
            sys.stderr.write('Error parsing json sent to POST /banhammer\n')


#debug(True)
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
        #qDate=e=pyes.MatchQuery("message",options.datePhrase,"phrase")
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
        #sys.stdout.write('{0}\n'.format(results.facets))

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
        # Look if attacker already in the DB, if yes get id
        dbcursor.execute("""SELECT id FROM blacklist_offender
              WHERE address = "%s" AND cidr = %d""" % (action['address'], int(action['cidr'])))
        qresult = dbcursor.fetchone()
        if not qresult:
            # insert new attacker in banhammer DB
            created_date = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
            dbcursor.execute("""
                INSERT INTO blacklist_offender(address, cidr, created_date, updated_date)
                VALUES ("%s", %d, '%s', '%s')
            """ % (action['address'], action['cidr'], created_date, created_date))
            # get the ID of this query
            dbcursor.execute("""SELECT id FROM blacklist_offender
              WHERE address = "%s" AND cidr = %d""" % (action['address'], int(action['cidr'])))
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
                INSERT INTO blacklist_blacklist(offender_id, start_date, end_date, comment, reporter, bug_number, removed)
                VALUES (%d, "%s", "%s", "%s", "%s", %d, 0)
                """ % (attacker_id, start_date, end_date, action['comment'], action['reporter'], int(action['bugid'])))
        else:
            dbcursor.execute("""
                INSERT INTO blacklist_blacklist(offender_id, start_date, end_date, comment, reporter, removed)
                VALUES (%d, "%s", "%s", "%s", "%s", 0)
                """ % (attacker_id, start_date, end_date, action['comment'], action['reporter']))
        mysqlconn.commit()
    except Exception as e:
        sys.stderr.write('Error while banhammering %s/%d: %s\n' % (action['address'], action['cidr'], e))


def initConfig():
    #change this to your default zone for when it's not specified
    options.defaultTimeZone = getConfig('defaulttimezone', 'US/Pacific',
        options.configfile)
    options.esservers = list(getConfig('esservers', 'http://localhost:9200',
        options.configfile).split(','))
    options.kibanaurl = getConfig('kibanaurl', 'http://localhost:9090',
        options.configfile)
    options.banhammerenable = getConfig('banhammerenable', False,
        options.configfile)
    options.banhammerdbhost = getConfig('banhammerdbhost', 'localhost',
        options.configfile)
    options.banhammerdbuser = getConfig('banhammerdbuser', 'root',
        options.configfile)
    options.banhammerdbpasswd = getConfig('banhammerdbpasswd', '',
        options.configfile)
    options.banhammerdbdb = getConfig('banhammerdbdb', 'banhammer',
        options.configfile)
    print(options)


if __name__ == "__main__":
    parser = OptionParser()
    parser.add_option("-c", dest='configfile',
        default=sys.argv[0].replace('.py', '.conf'),
        help="configuration file to use")
    (options, args) = parser.parse_args()
    initConfig()
    if options.banhammerenable:
        try:
            mysqlconn = MySQLdb.connect(
                host=options.banhammerdbhost,
                user=options.banhammerdbuser,
                passwd=options.banhammerdbpasswd,
                db=options.banhammerdbdb)
            dbcursor = mysqlconn.cursor()
        except Exception as e:
            sys.stderr.write('Failed to connect to the Banhammer DB\n')
    run(host="localhost", port=8081)
else:
    parser = OptionParser()
    parser.add_option("-c", dest='configfile',
        default=sys.argv[0].replace('.py', '.conf'),
        help="configuration file to use")
    (options, args) = parser.parse_args()
    initConfig()
    if (options.banhammerenable == 'true'):
        try:
            mysqlconn = MySQLdb.connect(
                host=options.banhammerdbhost,
                user=options.banhammerdbuser,
                passwd=options.banhammerdbpasswd,
                db=options.banhammerdbdb)
            dbcursor = mysqlconn.cursor()
        except Exception as e:
            sys.stderr.write('Failed to connect to the Banhammer DB\n')
    application = default_app()
