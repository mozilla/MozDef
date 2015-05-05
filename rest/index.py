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
import netaddr
import os
import pyes
import pytz
import pynsive
import requests
import sys
import socket
from bottle import debug, route, run, response, request, default_app, post
from datetime import datetime, timedelta
from configlib import getConfig, OptionParser
from elasticutils import S
from datetime import datetime
from datetime import timedelta
from dateutil.parser import parse
from ipwhois import IPWhois
from bson.son import SON
from operator import itemgetter
from pymongo import MongoClient
from bson import json_util

options = None
pluginList = list()   # tuple of module,registration dict,priority



def enable_cors(fn):
    ''' cors decorator for rest/ajax'''
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
def test():
    '''test endpoint for..testing'''
    ip = request.environ.get('REMOTE_ADDR')
    # response.headers['X-IP'] = '{0}'.format(ip)
    response.status = 200

    sendMessgeToPlugins(request, response, 'test')
    return response

@route('/status')
@route('/status/')
def status():
    '''endpoint for a status/health check'''
    if request.body:
        request.body.read()
        request.body.close()
    response.status = 200
    response.content_type = "application/json"
    response.body = json.dumps(dict(status='ok'))
    sendMessgeToPlugins(request, response, 'status')
    return response


@route('/ldapLogins')
@route('/ldapLogins/')
@enable_cors
def index():
    '''an endpoint to return success/failed login counts'''
    if request.body:
        request.body.read()
        request.body.close()
    response.content_type = "application/json"
    sendMessgeToPlugins(request, response, 'ldapLogins')
    return(esLdapResults())


@route('/veris')
@route('/veris/')
@enable_cors
def index():
    '''returns a count of veris tags'''
    if request.body:
        request.body.read()
        request.body.close()
    response.content_type = "application/json"
    response.body = verisSummary()
    sendMessgeToPlugins(request, response, 'veris')
    return response


@route('/kibanadashboards')
@route('/kibanadashboards/')
@enable_cors
def index():
    '''returns a list of dashboards to show on the UI'''
    if request.body:
        request.body.read()
        request.body.close()

    response.content_type = "application/json"
    response.body = kibanaDashboards()
    sendMessgeToPlugins(request, response, 'kibanadashboards')
    return response


@post('/blockip', methods=['POST'])
@post('/blockip/', methods=['POST'])
@enable_cors
def index():
    '''will receive a call to block an ip address'''
    sendMessgeToPlugins(request, response, 'blockip')
    return response


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

    if 'ipaddress' in requestDict.keys() and isIPv4(requestDict['ipaddress']):
        response.content_type = "application/json"
        response.body = getWhois(requestDict['ipaddress'])
    else:
        response.status = 500

    sendMessgeToPlugins(request, response, 'ipwhois')
    return response


@post('/ipintel', methods=['POST'])
@post('/ipintel/', methods=['POST'])
@enable_cors
def ipintel():
    '''send an IP address through plugins for intel enhancement'''
    if request.body:
        arequest = request.body.read()
        #request.body.close()
    # valid json?
    try:
        requestDict = json.loads(arequest)
    except ValueError as e:
        response.status = 500
    if 'ipaddress' in requestDict.keys() and isIPv4(requestDict['ipaddress']):
        response.content_type = "application/json"
    else:
        response.status = 500

    sendMessgeToPlugins(request, response, 'ipintel')
    return response


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

    if 'ipaddress' in requestDict.keys() and isIPv4(requestDict['ipaddress']):
        response.content_type = "application/json"
        response.body = getIPCIF(requestDict['ipaddress'])
    else:
        response.status = 500

    sendMessgeToPlugins(request, response, 'ipcifquery')
    return response

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
            response.body = dresponse.content
        else:
            response.status = dresponse.status_code

    else:
        response.status = 500

    sendMessgeToPlugins(request, response, 'ipdshieldquery')
    return response

@route('/plugins', methods=['GET'])
@route('/plugins/', methods=['GET'])
@route('/plugins/<endpoint>', methods=['GET'])
def getPluginList(endpoint=None):
    ''' return a json representation of the plugin tuple
        (mname, mclass, mreg, mpriority)
         minus the actual class (which isn't json-able)
         for all plugins, or for a specific endpoint
    '''
    pluginResponse = list()
    if endpoint is None:
        for plugin in pluginList:
            pdict = {}
            pdict['file'] = plugin[0]
            pdict['name'] = plugin[1]
            pdict['description'] = plugin[2]
            pdict['registration'] = plugin[3]
            pdict['priority'] = plugin[4]
            pluginResponse.append(pdict)
    else:
        # filter the list to just the endpoint requested
        for plugin in pluginList:
            if endpoint in plugin[3]:
                pdict = {}
                pdict['file'] = plugin[0]
                pdict['name'] = plugin[1]
                pdict['description'] = plugin[2]
                pdict['registration'] = plugin[3]
                pdict['priority'] = plugin[4]
                pluginResponse.append(pdict)
    response.content_type = "application/json"
    response.body = json.dumps(pluginResponse)

    sendMessgeToPlugins(request, response, 'plugins')
    return response


def registerPlugins():
    '''walk the ./plugins directory
       and register modules in pluginList
       as a tuple: (mfile, mname, mdescription, mreg, mpriority, mclass)
    '''

    plugin_manager = pynsive.PluginManager()
    if os.path.exists('plugins'):
        modules = pynsive.list_modules('plugins')
        for mfile in modules:
            module = pynsive.import_module(mfile)
            reload(module)
            if not module:
                raise ImportError('Unable to load module {}'.format(mfile))
            else:
                if 'message' in dir(module):
                    mclass = module.message()
                    mreg = mclass.registration
                    mclass.restoptions = options

                    if 'priority' in dir(mclass):
                        mpriority = mclass.priority
                    else:
                        mpriority = 100
                    if 'name' in dir(mclass):
                        mname = mclass.name
                    else:
                        mname = mfile

                    if 'description' in dir(mclass):
                        mdescription = mclass.description
                    else:
                        mdescription = mfile

                    if isinstance(mreg, list):
                        print('[*] plugin {0} registered to receive messages from /{1}'.format(mfile, mreg))
                        pluginList.append((mfile, mname, mdescription, mreg, mpriority, mclass))


def sendMessgeToPlugins(request, response, endpoint):
    '''
       iterate the registered plugins
       sending the response/request to any that have
       registered for this rest endpoint
    '''
    # sort by priority
    for plugin in sorted(pluginList, key=itemgetter(4), reverse=False):
        if endpoint in plugin[3]:
            (request, response) = plugin[5].onMessage(request, response)


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

def esLdapResults(begindateUTC=None, enddateUTC=None):
    '''an ES query/facet to count success/failed logins'''
    resultsList = list()
    if begindateUTC is None:
        begindateUTC = datetime.now() - timedelta(hours=1)
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


def getWhois(ipaddress):
    try:
        whois = dict()
        ip = netaddr.IPNetwork(ipaddress)[0]
        if (not ip.is_loopback() and not ip.is_private() and not ip.is_reserved()):
            whois = IPWhois(netaddr.IPNetwork(ipaddress)[0]).lookup()

        whois['fqdn']=socket.getfqdn(str(netaddr.IPNetwork(ipaddress)[0]))
        return (json.dumps(whois))
    except Exception as e:
        sys.stderr.write('Error looking up whois for {0}: {1}\n'.format(ipaddress, e))


def getIPCIF(ipaddress):
    ''' query a CIF service for information on this IP address per:
        https://code.google.com/p/collective-intelligence-framework/wiki/API_HTTP_v1
    '''
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

def verisSummary(verisRegex=None):
    try:
        # aggregate the veris tags from the incidents collection and return as json
        client = MongoClient(options.mongohost, options.mongoport)
        # use meteor db
        incidents= client.meteor['incidents']
        #iveris=incidents.aggregate([
                                   #{"$match":{"tags":{"$exists":True}}},
                                   #{"$unwind" : "$tags" },
                                   #{"$match":{"tags":{"$regex":''}}}, #regex for tag querying
                                   #{"$group": {"_id": "$tags", "hitcount": {"$sum": 1}}}, # count by tag
                                   #{"$sort": SON([("hitcount", -1), ("_id", -1)])}, #sort
                                   #])

        iveris=incidents.aggregate([

                                   {"$match":{"tags":{"$exists":True}}},
                                   {"$unwind" : "$tags" },
                                   {"$match":{"tags":{"$regex":''}}}, #regex for tag querying
                                   { "$project" : { "dateOpened" : 1 ,
                                                   "tags" : 1 ,
                                                   "phase": 1,
                                                   "_id": 0
                                                   } }
                                   ])
        if 'ok' in iveris.keys() and 'result' in iveris.keys():
            return json.dumps(iveris['result'], default=json_util.default)
        else:
            return json.dumps(list())
    except Exception as e:
            sys.stderr.write('Exception while aggregating veris summary: {0}\n'.format(e))

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

    # options for your CIF service
    options.cifapikey = getConfig('cifapikey', '', options.configfile)
    options.cifhosturl = getConfig('cifhosturl',
                                   'http://localhost/',
                                   options.configfile)
    # mongo connectivity options
    options.mongohost = getConfig('mongohost', 'localhost', options.configfile)
    options.mongoport = getConfig('mongoport', 3001, options.configfile)


if __name__ == "__main__":
    parser = OptionParser()
    parser.add_option("-c", dest='configfile',
        default=sys.argv[0].replace('.py', '.conf'),
        help="configuration file to use")
    (options, args) = parser.parse_args()
    initConfig()
    registerPlugins()

    run(host="localhost", port=8081)
else:
    parser = OptionParser()
    parser.add_option("-c", dest='configfile',
        default=sys.argv[0].replace('.py', '.conf'),
        help="configuration file to use")
    (options, args) = parser.parse_args()
    initConfig()
    registerPlugins()

    application = default_app()
