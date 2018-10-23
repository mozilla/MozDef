# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
# Copyright (c) 2014 Mozilla Corporation

import bottle
import json
import netaddr
import os
import pynsive
import random
import re
import requests
import sys
import socket
from bottle import route, run, response, request, default_app, post
from datetime import datetime, timedelta
from configlib import getConfig, OptionParser
from ipwhois import IPWhois
from operator import itemgetter
from pymongo import MongoClient
from bson import json_util

from mozdef_util.elasticsearch_client import ElasticsearchClient, ElasticsearchInvalidIndex
from mozdef_util.query_models import SearchQuery, TermMatch, RangeMatch, Aggregation

from mozdef_util.utilities.toUTC import toUTC
from mozdef_util.utilities.logger import logger, initLogger


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
    response.body = json.dumps(dict(status='ok', service='restapi'))
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

@post('/blockfqdn', methods=['POST'])
@post('/blockfqdn/', methods=['POST'])
@enable_cors
def index():
    '''will receive a call to block an ip address'''
    sendMessgeToPlugins(request, response, 'blockfqdn')
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

        headers = {
            'User-Agent': options.user_agent
        }

        dresponse = requests.get('{0}{1}?json'.format(url, requestDict['ipaddress']), headers=headers)
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

@post('/incident', methods=['POST'])
@post('/incident/', methods=['POST'])
def createIncident():
    '''
    endpoint to create an incident

    request body eg.
    {
        "summary": <string>,
        "phase": <enum: case-insensitive>
                        Choose from ('Identification', 'Containment', 'Eradication',
                                     'Recovery', 'Lessons Learned', 'Closed')
        "creator": <email>,

        // Optional Arguments

        "description": <string>,
        "dateOpened": <string: yyyy-mm-dd hh:mm am/pm>,
        "dateClosed": <string: yyyy-mm-dd hh:mm am/pm>,
        "dateReported": <string: yyyy-mm-dd hh:mm am/pm>,
        "dateVerified": <string: yyyy-mm-dd hh:mm am/pm>,
        "dateMitigated": <string: yyyy-mm-dd hh:mm am/pm>,
        "dateContained": <string: yyyy-mm-dd hh:mm am/pm>,
        "tags": <list <string>>,
        "references": <list <string>>
    }
    '''

    client = MongoClient(options.mongohost, options.mongoport)
    incidentsMongo = client.meteor['incidents']

    response.content_type = "application/json"
    EMAIL_REGEX = r"^[A-Za-z0-9\.\+_-]+@[A-Za-z0-9\._-]+\.[a-zA-Z]*$"

    if not request.body:
        response.status = 500
        response.body = json.dumps(dict(status='failed',
                                        error='No data provided'))

        return response

    try:
        body = json.loads(request.body.read())
        request.body.close()
    except ValueError:
        response.status = 500
        response.body = json.dumps(dict(status='failed',
                                        error='Invalid JSON'))

        return response

    incident = dict()

    validIncidentPhases = ('Identification', 'Containment', 'Eradication',
                           'Recovery', 'Lessons Learned', 'Closed')

    incident['_id'] = generateMeteorID()
    try:
        incident['summary'] = body['summary']
        incident['phase'] = body['phase']
        incident['creator'] = body['creator']
        incident['creatorVerified'] = False
    except KeyError:
        response.status = 500
        response.body = json.dumps(dict(status='failed',
                                        error='Missing required keys'
                                              '(summary, phase, creator)'))
        return response

    # Validating Incident phase type
    if (type(incident['phase']) not in (str, unicode) or
        incident['phase'] not in validIncidentPhases):

        response.status = 500
        response.body = json.dumps(dict(status='failed',
                                        error='Invalid incident phase'))
        return response

    # Validating creator email
    if not re.match(EMAIL_REGEX, incident['creator']):
        response.status = 500
        response.body = json.dumps(dict(status='failed',
                                        error='Invalid creator email'))
        return response

    incident['description'] = body.get('description')
    incident['dateOpened'] = validateDate(body.get('dateOpened', datetime.now()))
    incident['dateClosed'] = validateDate(body.get('dateClosed'))
    incident['dateReported'] = validateDate(body.get('dateReported'))
    incident['dateVerified'] = validateDate(body.get('dateVerified'))
    incident['dateMitigated'] = validateDate(body.get('dateMitigated'))
    incident['dateContained'] = validateDate(body.get('dateContained'))

    dates = [incident['dateOpened'],
              incident['dateClosed'],
              incident['dateReported'],
              incident['dateVerified'],
              incident['dateMitigated'],
              incident['dateContained']]

    # Validating all the dates for the format
    if False in dates:
        response.status = 500
        response.body = json.dumps(dict(status='failed',
                                        error='Wrong format of date. Please '
                                              'use yyyy-mm-dd hh:mm am/pm'))
        return response

    incident['tags'] = body.get('tags')

    if incident['tags'] and type(incident['tags']) is not list:
        response.status = 500
        response.body = json.dumps(dict(status='failed',
                                        error='tags field must be a list'))
        return response

    incident['references'] = body.get('references')

    if incident['references'] and type(incident['references']) is not list:
        response.status = 500
        response.body = json.dumps(dict(status='failed',
                                        error='references field must be a list'))
        return response

    # Inserting incident dict into mongodb
    try:
        incidentsMongo.insert(incident)
    except Exception as err:
        response.status = 500
        response.body = json.dumps(dict(status='failed',
                                        error=err))
        return response

    response.status = 200
    response.body = json.dumps(dict(status='success',
                                    message='Incident: <{}> added.'.format(
                                        incident['summary'])
                                    ))
    return response

def validateDate(date, dateFormat='%Y-%m-%d %I:%M %p'):
    '''
    Converts a date string into a datetime object based
    on the dateFormat keyworded arg.
    Default dateFormat: %Y-%m-%d %I:%M %p (example: 2015-10-21 2:30 pm)
    '''

    dateObj = None

    if type(date) == datetime:
        return date

    try:
        dateObj = datetime.strptime(date, dateFormat)
    except ValueError:
        dateObj = False
    except TypeError:
        dateObj = None
    finally:
        return dateObj

def generateMeteorID():
    return('%024x' % random.randrange(16**24))

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
                        logger.info('[*] plugin {0} registered to receive messages from /{1}'.format(mfile, mreg))
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
        es_client = ElasticsearchClient(list('{0}'.format(s) for s in options.esservers))
        search_query = SearchQuery()
        range_match = RangeMatch('utctimestamp', begindateUTC, enddateUTC)

        search_query.add_must(range_match)
        search_query.add_must(TermMatch('tags', 'ldap'))

        search_query.add_must(TermMatch('details.result', 'LDAP_INVALID_CREDENTIALS'))

        search_query.add_aggregation(Aggregation('details.result'))
        search_query.add_aggregation(Aggregation('details.dn'))

        results = search_query.execute(es_client, indices=['events'])

        stoplist = ('o', 'mozilla', 'dc', 'com', 'mozilla.com', 'mozillafoundation.org', 'org', 'mozillafoundation')

        for t in results['aggregations']['details.dn']['terms']:
            if t['key'] in stoplist:
                continue
            failures = 0
            success = 0
            dn = t['key']

            details_query = SearchQuery()
            details_query.add_must(range_match)
            details_query.add_must(TermMatch('tags', 'ldap'))
            details_query.add_must(TermMatch('details.dn', dn))
            details_query.add_aggregation(Aggregation('details.result'))

            results = details_query.execute(es_client)

            for t in results['aggregations']['details.result']['terms']:
                if t['key'].upper() == 'LDAP_SUCCESS':
                    success = t['count']
                if t['key'].upper() == 'LDAP_INVALID_CREDENTIALS':
                    failures = t['count']
            resultsList.append(dict(dn=dn, failures=failures,
                success=success, begin=begindateUTC.isoformat(),
                end=enddateUTC.isoformat()))

        return(json.dumps(resultsList))
    except Exception as e:
        sys.stderr.write('Error trying to get ldap results: {0}\n'.format(e))


def kibanaDashboards():
    resultsList = []
    try:
        es_client = ElasticsearchClient((list('{0}'.format(s) for s in options.esservers)))
        search_query = SearchQuery()
        search_query.add_must(TermMatch('_type', 'dashboard'))
        results = search_query.execute(es_client, indices=['.kibana'])

        for dashboard in results['hits']:
            resultsList.append({
                'name': dashboard['_source']['title'],
                'url': "%s#/%s/%s" % (options.kibanaurl,
                "dashboard",
                dashboard['_id'])
            })

    except ElasticsearchInvalidIndex as e:
        sys.stderr.write('Kibana dashboard index not found: {0}\n'.format(e))

    except Exception as e:
        sys.stderr.write('Kibana dashboard received error: {0}\n'.format(e))

    return json.dumps(resultsList)


def getWhois(ipaddress):
    try:
        whois = dict()
        ip = netaddr.IPNetwork(ipaddress)[0]
        if (not ip.is_loopback() and not ip.is_private() and not ip.is_reserved()):
            whois = IPWhois(netaddr.IPNetwork(ipaddress)[0]).lookup_whois()

        whois['fqdn']=socket.getfqdn(str(netaddr.IPNetwork(ipaddress)[0]))
        return (json.dumps(whois))
    except Exception as e:
        sys.stderr.write('Error looking up whois for {0}: {1}\n'.format(ipaddress, e))


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
                                   {"$unwind": "$tags"},
                                   {"$match":{"tags":{"$regex":''}}},  # regex for tag querying
                                   {"$project": {"dateOpened": 1,
                                                   "tags": 1,
                                                   "phase": 1,
                                                   "_id": 0
                                                   }}
                                   ])
        if iveris:
            return json.dumps(list(iveris), default=json_util.default)
        else:
            return json.dumps(list())
    except Exception as e:
            sys.stderr.write('Exception while aggregating veris summary: {0}\n'.format(e))

def initConfig():
    # output our log to stdout or syslog
    options.output = getConfig('output', 'stdout', options.configfile)
    options.sysloghostname = getConfig('sysloghostname', 'localhost', options.configfile)
    options.syslogport = getConfig('syslogport', 514, options.configfile)
    options.esservers = list(getConfig('esservers',
                                       'http://localhost:9200',
                                       options.configfile).split(','))
    options.kibanaurl = getConfig('kibanaurl',
                                  'http://localhost:9090',
                                  options.configfile)

    # mongo connectivity options
    options.mongohost = getConfig('mongohost', 'localhost', options.configfile)
    options.mongoport = getConfig('mongoport', 3001, options.configfile)

    options.listen_host = getConfig('listen_host', '127.0.0.1', options.configfile)

    default_user_agent = 'Mozilla/5.0 (X11; Linux x86_64; rv:10.0) Gecko/20100101 Firefox/58.0'
    options.user_agent = getConfig('user_agent', default_user_agent, options.configfile)

parser = OptionParser()
parser.add_option("-c", dest='configfile',
    default=os.path.join(os.path.dirname(__file__), __file__).replace('.py', '.conf'),
    help="configuration file to use")
(options, args) = parser.parse_args()
initConfig()
initLogger(options)
registerPlugins()

if __name__ == "__main__":
    run(host=options.listen_host, port=8081)
else:
    application = default_app()
