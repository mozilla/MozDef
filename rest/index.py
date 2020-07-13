# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# Copyright (c) 2014 Mozilla Corporation

import bottle
import enum
import json
import netaddr
import os
import pynsive
import random
import re
import requests
import socket
import importlib
from bottle import route, run, response, request, default_app, post, put, delete, get
from datetime import datetime, timedelta
from configlib import getConfig, OptionParser
from ipwhois import IPWhois
from operator import itemgetter
from pymongo import MongoClient
from bson import json_util
from bson.codec_options import CodecOptions

from mozdef_util.elasticsearch_client import ElasticsearchClient, ElasticsearchInvalidIndex
from mozdef_util.query_models import SearchQuery, TermMatch

from mozdef_util.utilities.logger import logger, initLogger
from mozdef_util.utilities.toUTC import toUTC


options = None
pluginList = list()   # tuple of module,registration dict,priority

# The name of the MongoDB database that stores duplicate chains.
DUP_CHAIN_DB = "duplicatechains"


class StatusCode(enum.IntEnum):
    """A simple enumeration of common status codes.
    """

    OK = 200
    BAD_REQUEST = 400
    INTERNAL_ERROR = 500


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
    # ip = request.environ.get('REMOTE_ADDR')
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


@route('/getwatchlist')
@route('/getwatchlist/')
def status():
    '''endpoint for grabbing watchlist contents'''
    if request.body:
        request.body.read()
        request.body.close()
    response.status = 200
    response.content_type = "application/json"
    response.body = getWatchlist()
    return response


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


@post('/watchitem', methods=['POST'])
@post('/watchitem/', methods=['POST'])
@enable_cors
def index():
    '''will receive a call to watchlist a specific term'''
    sendMessgeToPlugins(request, response, 'watchitem')
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
    except ValueError:
        response.status = 500

    if 'ipaddress' in requestDict and isIPv4(requestDict['ipaddress']):
        response.content_type = "application/json"
        response.body = getWhois(requestDict['ipaddress'])
    else:
        response.status = 500

    sendMessgeToPlugins(request, response, 'ipwhois')
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
    except ValueError:
        response.status = 500
        return
    if 'ipaddress' in requestDict and isIPv4(requestDict['ipaddress']):
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


@route('/alertschedules')
@route('/alertschedules/')
@enable_cors
def index():
    '''an endpoint to return alert schedules'''
    if request.body:
        request.body.read()
        request.body.close()
    response.content_type = "application/json"
    mongoclient = MongoClient(options.mongohost, options.mongoport)
    schedulers_db = mongoclient.meteor['alertschedules'].with_options(codec_options=CodecOptions(tz_aware=True))

    mongodb_alerts = schedulers_db.find()
    alert_schedules_dict = {}
    for mongodb_alert in mongodb_alerts:
        if mongodb_alert['last_run_at']:
            mongodb_alert['last_run_at'] = mongodb_alert['last_run_at'].isoformat()
        if 'modifiedat' in mongodb_alert:
            mongodb_alert['modifiedat'] = mongodb_alert['modifiedat'].isoformat()
        alert_schedules_dict[mongodb_alert['name']] = mongodb_alert

    response.body = json.dumps(alert_schedules_dict)
    response.status = 200
    return response


@post('/syncalertschedules', methods=['POST'])
@post('/syncalertschedules/', methods=['POST'])
@enable_cors
def sync_alert_schedules():
    '''an endpoint to return alerts schedules'''
    if not request.body:
        response.status = 503
        return response

    alert_schedules = json.loads(request.body.read())
    request.body.close()

    response.content_type = "application/json"
    mongoclient = MongoClient(options.mongohost, options.mongoport)
    schedulers_db = mongoclient.meteor['alertschedules'].with_options(codec_options=CodecOptions(tz_aware=True))
    results = schedulers_db.find()
    for result in results:
        if result['name'] in alert_schedules:
            new_sched = alert_schedules[result['name']]
            result['total_run_count'] = new_sched['total_run_count']
            result['last_run_at'] = new_sched['last_run_at']
            if result['last_run_at']:
                result['last_run_at'] = toUTC(result['last_run_at'])
            logger.debug("Inserting schedule for {0} into mongodb".format(result['name']))
            schedulers_db.save(result)

    response.status = 200
    return response


@post('/updatealertschedules', methods=['POST'])
@post('/updatealertschedules/', methods=['POST'])
@enable_cors
def update_alert_schedules():
    '''an endpoint to return alerts schedules'''
    if not request.body:
        response.status = 503
        return response

    alert_schedules = json.loads(request.body.read())
    request.body.close()

    response.content_type = "application/json"
    mongoclient = MongoClient(options.mongohost, options.mongoport)
    schedulers_db = mongoclient.meteor['alertschedules'].with_options(codec_options=CodecOptions(tz_aware=True))
    schedulers_db.remove()

    for alert_name, alert_schedule in alert_schedules.items():
        if alert_schedule['last_run_at']:
            alert_schedule['last_run_at'] = toUTC(alert_schedule['last_run_at'])
        logger.debug("Inserting schedule for {0} into mongodb".format(alert_name))
        schedulers_db.insert(alert_schedule)

    response.status = 200
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
    if (type(incident['phase']) is not str or
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

    dates = [
        incident['dateOpened'],
        incident['dateClosed'],
        incident['dateReported'],
        incident['dateVerified'],
        incident['dateMitigated'],
        incident['dateContained']
    ]

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


@post("/alertstatus")
@post("/alertstatus/")
def update_alert_status():
    """Update the status of an alert.

    Requests are expected to take the following (JSON) form:

    ```
    {
        "alert": str,
        "status": str,
        "user": {
            "email": str,
            "slack": str
        },
        "identityConfidence": str
        "response": str
    }
    ```

    Where:
        * `"alert"` is the unique identifier fo the alert whose status
        we are to update.
        * `"status"` is one of "manual", "inProgress", "acknowledged"
        or "escalated".
        * `identityConfidence` is one of "highest", "high", "moderate", "low",
        or "lowest".


    This function writes back a response containing the following JSON.

    ```
    {
        "error": Optional[str]
    }
    ```

    If an error occurs and the alert is not able to be updated, then
    the "error" field will contain a string message describing the issue.
    Otherwise, this field will simply be `null`.  This function will,
    along with updating the alert's status, append information about the
    user and their response to `alert['details']['triage']`.

    Responses will also use status codes to indicate success / failure / error.
    """

    initConfig()

    mongo = MongoClient(options.mongohost, options.mongoport)
    alerts = mongo.meteor["alerts"]

    try:
        req = json.loads(request.body.read())
        request.body.close()
    except ValueError:
        response.status = StatusCode.BAD_REQUEST
        return {
            "error": "Missing or invalid request body"
        }

    valid_statuses = ["manual", "inProgress", "acknowledged", "escalated"]

    if req.get("status") not in valid_statuses:
        required = " or ".join(valid_statuses)

        response.status = StatusCode.BAD_REQUEST
        return {
            "error": "Status not one of {}".format(required),
        }

    expected_fields = ["alert", "user", "response", "identityConfidence"]

    if any([req.get(field) is None for field in expected_fields]):
        required = ", ".join(expected_fields)

        response.status = StatusCode.BAD_REQUEST
        return {
            "error": "Missing a required field, one of {}".format(required),
        }

    valid_confidences = ["highest", "high", "moderate", "low", "lowest"]

    if req.get("identityConfidence") not in valid_confidences:
        required = " or ".join(valid_confidences)

        response.status = StatusCode.BAD_REQUEST
        return {
            "error": "identityConfidence not one of {}".format(required),
        }

    details = {
        "triage": {
            "user": req.get("user"),
            "response": req.get("response"),
        },
        "identityConfidence": req.get("identityConfidence"),
    }

    fields_to_update = {
        "status": req.get("status"),
        "details": details,
    }

    if req.get("status") == "acknowledged":
        fields_to_update.update({
            "acknowledged": toUTC(datetime.utcnow()),
            "acknowledgedby": "triagebot",
        })

    modified_count = alerts.update_one(
        {"esmetadata.id": req.get("alert")}, {"$set": fields_to_update}
    ).modified_count

    if modified_count != 1:
        response.status = StatusCode.BAD_REQUEST
        return {"error": "Alert not found"}

    response.status = StatusCode.OK
    return {"error": None}

    return response


@get("/alerttriagechain")
@get("/alerttriagechain/")
def retrieve_duplicate_chain():
    """Search for a `Duplicate Chain` storing information about duplicate
    alerts triggered by the same user's activity.  These chains track such
    duplicate alerts so that the triage bot does not have to message a user
    on Slack for each such alert within some period of time.

    Requests are expected to include the following query parameters.

        * `"alert": str` is the "label" for the alert, signifying which of the
        supported alerts the user in question triggered.
        * `"user": str` is the email address of the user contacted.

    This function writes back a response containing the following JSON.

    ```
    {
        "error": Optional[str],
        "identifiers": List[str],
        "created": str,
        "modified": str
    }
    ```

    Here,
        * `"error"` will contain a string message if any error occurs performing
        a lookup.  If such an error occurs, `"identifiers"` will be an empty
        list.
        * `"identifiers"` is a list of IDs of alerts stored under the chain.
        * `"created"` is the date & time at which the chain was created.
        * `"modified"` is the date & time at which the chain was last modified.

    Both the `"created"` and `"modified"` fields represent UTC timestamps and
    are formatted like `YYYY/mm/dd HH:MM:SS`.
    """

    initConfig()

    mongo = MongoClient(options.mongohost, options.mongoport)
    dupchains = mongo.meteor[DUP_CHAIN_DB]

    def _error(msg):
        return json.dumps({
            "error": msg,
            "identifiers": [],
            "created": toUTC(datetime.utcnow()).isoformat(),
            "modified": toUTC(datetime.utcnow()).isoformat(),
        })

    query = {"alert": request.query.alert, "user": request.query.user}

    if query.get("alert", "") == "" or query.get("user", "") == "":
        response.status = StatusCode.BAD_REQUEST
        response.body = _error("Request missing `alert` or `user` field")
        return response

    chain = dupchains.find_one(query)

    if chain is None:
        # This is not an error, but we do want to write an empty response.
        response.status = StatusCode.OK
        response.body = _error("Did not find requested duplicate chian")
        return response

    response.status = StatusCode.OK
    return {
        "error": None,
        "identifiers": chain["identifiers"],
        "created": toUTC(chain["created"]).isoformat(),
        "modified": toUTC(chain["modified"]).isoformat(),
    }


@post("/alerttriagechain")
@post("/alerttriagechain/")
def create_duplicate_chain():
    """Create a 'Duplicate Chain', linking information about alerts being
    handled by the Triage Bot so that a user's response to a message about
    one alert can be replicated against duplicate alerts without sending
    multiple messages.

    Requests are expected to take the following (JSON) form:

    ```
    {
        "alert": str,
        "user": str,
        "identifiers": List[str]
    }
    ```

    Where:
        * `"alert"` is the "label" for the alert, signifying which of the
        supported alerts is being triaged.
        * `"user"` is the email address of the user contacted.
        * `"identifier"` is a list of ElasticSearch IDs of alerts of the
        same kind triggered by the same user.

    This function writes back a response containing the following JSON.

    ```
    {
        "error": Optional[str]
    }
    ```

    If an error occurs, a duplicate chain will not be created and an error
    string will be returned.  Otherwise, the `error` field will be `null.`
    """

    initConfig()

    mongo = MongoClient(options.mongohost, options.mongoport)
    dupchains = mongo.meteor[DUP_CHAIN_DB]

    try:
        req = request.json
    except bottle.HTTPError:
        response.status = StatusCode.BAD_REQUEST
        return {"error": "Missing or invalid request body"}

    now = datetime.utcnow()

    chain = {
        "alert": req.get("alert"),
        "user": req.get("user"),
        "identifiers": req.get("identifiers", []),
        "created": now,
        "modified": now,
    }

    if chain["alert"] is None or chain["user"] is None:
        response.status = StatusCode.BAD_REQUEST
        return {
            "error": "Request missing required key `alert` or `user`"
        }

    result = dupchains.insert_one(chain)
    if not result.acknowledged:
        response.status = StatusCode.INTERNAL_ERROR
        return {"error": "Failed to store new duplicate chain"}

    response.status = StatusCode.OK
    return {"error": None}


@put("/alerttriagechain")
@put("/alerttriagechain/")
def update_duplicate_chain():
    """Update a `DuplicateChain`, appending information about a new alert
    destined for a Slack user via the triage Bot.
    See `create_duplicate_chain` for more information.

    Requests are expected to take the following (JSON) form:

    ```
    {
        "alert": str,
        "user": str,
        "identifiers": List[str]
    }
    ```

    The parameters are the same as those of `create_duplicate_chain`.

    This function writes back a response containing the following JSON.

    ```
    {
        "error": Optional[str]
    }
    ```

    If an error occurs, no duplicate chains will be updated.  This endpoint
    does not create a new chain if one does not already exist.
    """

    initConfig()

    mongo = MongoClient(options.mongohost, options.mongoport)
    dupchains = mongo.meteor[DUP_CHAIN_DB]

    try:
        req = request.json
    except bottle.HTTPError:
        response.status = StatusCode.BAD_REQUEST
        return {"error": "Missing or invalid request body"}

    query = {"alert": req.get("alert"), "user": req.get("user")}

    new_ids = req.get("identifiers")

    if any([x is None for x in (query["alert"], query["user"], new_ids)]):
        response.status = StatusCode.BAD_REQUEST
        return {
            "error": "Request missing required key `alert`, `user` or "
            "`identifiers`"
        }

    chain = dupchains.find_one(query)

    if chain is None:
        response.status = StatusCode.BAD_REQUEST
        return {"error": "Duplicate chain does not exist"}

    modified = dupchains.update_one(
        query,
        {
            "$set": {
                "identifiers": chain["identifiers"] + new_ids,
                "modified": datetime.utcnow(),
            }
        },
    ).modified_count

    if modified != 1:
        response.status = StatusCode.INTERNAL_ERROR
        return {"error": "Failed to update chain"}
        return response

    response.status = StatusCode.OK
    return {"error": None}


@delete("/alerttriagechain")
@delete("/alerttriagechain/")
def delete_duplicate_chain():
    """Deletes a Duplicate Chain tracking duplicate alerts triggered by the
    same user.

    Requests are expected to contain the following JSON data:

    ```
    {
        "alert": str,
        "user": str
    }
    ```

    Where:
        * `"alert"` is the label of an alert supported by the triage bot.
        * `"user"` is the email address of the user the triage bot contacted.

    Responses will contain the following JSON:

    ```
    {
        "error": Optional[str]
    }
    ```

    In the case that a duplicate chain identified by the request parameters does
    not exist or an error occurs in deleting it, the `"error"` field will
    contain a string describing the error.  Otherwise, it is `null`.
    """

    initConfig()

    mongo = MongoClient(options.mongohost, options.mongoport)
    dupchains = mongo.meteor[DUP_CHAIN_DB]

    try:
        req = request.json
    except bottle.HTTPError:
        response.status = StatusCode.BAD_REQUEST
        return {"error": "Missing or invalid request body"}

    query = {"alert": req.get("alert"), "user": req.get("user")}

    if query["alert"] is None or query["user"] is None:
        response.status = StatusCode.BAD_REQUEST
        return {
            "error": "Request missing required key `alert` or `user`"
        }

    result = dupchains.delete_one(query)

    if not result.acknowledged:
        response.status = StatusCode.BAD_REQUEST
        return {"error": "No such duplicate chain exists"}

    response.status = StatusCode.OK
    return {"error": None}


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
    '''walk the plugins directory
       and register modules in pluginList
       as a tuple: (mfile, mname, mdescription, mreg, mpriority, mclass)
    '''

    plugin_location = os.path.join(os.path.dirname(__file__), "plugins")
    module_name = os.path.basename(plugin_location)
    root_plugin_directory = os.path.join(plugin_location, '..')

    plugin_manager = pynsive.PluginManager()
    plugin_manager.plug_into(root_plugin_directory)

    if os.path.exists(plugin_location):
        modules = pynsive.list_modules(module_name)
        for mfile in modules:
            module = pynsive.import_module(mfile)
            importlib.reload(module)
            if not module:
                raise ImportError('Unable to load module {}'.format(mfile))
            else:
                if 'message' in dir(module):
                    mclass = module.message()
                    mreg = mclass.registration
                    mclass.restoptions = options.__dict__

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


def kibanaDashboards():
    resultsList = []
    try:
        es_client = ElasticsearchClient((list('{0}'.format(s) for s in options.esservers)))
        search_query = SearchQuery()
        search_query.add_must(TermMatch('type', 'dashboard'))
        results = search_query.execute(es_client, indices=['.kibana'])

        for dashboard in results['hits']:
            dashboard_id = dashboard['_id']
            if dashboard_id.startswith('dashboard:'):
                dashboard_id = dashboard_id.replace('dashboard:', '')

            resultsList.append({
                'name': dashboard['_source']['dashboard']['title'],
                'id': dashboard_id
            })

    except ElasticsearchInvalidIndex as e:
        logger.error('Kibana dashboard index not found: {0}\n'.format(e))

    except Exception as e:
        logger.error('Kibana dashboard received error: {0}\n'.format(e))

    return json.dumps(resultsList)


def getWatchlist():
    WatchList = []
    try:
        # connect to mongo
        client = MongoClient(options.mongohost, options.mongoport)
        mozdefdb = client.meteor
        watchlistentries = mozdefdb['watchlist']

        # Log the entries we are removing to maintain an audit log
        expired = watchlistentries.find({'dateExpiring': {"$lte": datetime.utcnow() - timedelta(hours=1)}})
        for entry in expired:
            logger.debug('Deleting entry {0} from watchlist /n'.format(entry))

        # delete any that expired
        watchlistentries.delete_many({'dateExpiring': {"$lte": datetime.utcnow() - timedelta(hours=1)}})

        # Lastly, export the combined watchlist
        watchCursor=mozdefdb['watchlist'].aggregate([
            {"$sort": {"dateAdded": -1}},
            {"$match": {"watchcontent": {"$exists": True}}},
            {"$match":
                {"$or":[
                    {"dateExpiring": {"$gte": datetime.utcnow()}},
                    {"dateExpiring": {"$exists": False}},
                ]},
             },
            {"$project":{"watchcontent":1}},
        ])
        for content in watchCursor:
            WatchList.append(
                content['watchcontent']
            )
        return json.dumps(WatchList)
    except ValueError as e:
        logger.error('Exception {0} collecting watch list\n'.format(e))


def getWhois(ipaddress):
    try:
        whois = dict()
        ip = netaddr.IPNetwork(ipaddress)[0]
        if (not ip.is_loopback() and not ip.is_private() and not ip.is_reserved()):
            whois = IPWhois(netaddr.IPNetwork(ipaddress)[0]).lookup_whois()

        whois['fqdn']=socket.getfqdn(str(netaddr.IPNetwork(ipaddress)[0]))
        return (json.dumps(whois))
    except Exception as e:
        logger.error('Error looking up whois for {0}: {1}\n'.format(ipaddress, e))


def verisSummary(verisRegex=None):
    try:
        # aggregate the veris tags from the incidents collection and return as json
        client = MongoClient(options.mongohost, options.mongoport)
        # use meteor db
        incidents = client.meteor['incidents']

        iveris = incidents.aggregate([
            {"$match": {"tags": {"$exists": True}}},
            {"$unwind": "$tags"},
            {"$match": {"tags": {"$regex": ''}}},
            {"$project": {
                "dateOpened": 1,
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
            logger.error('Exception while aggregating veris summary: {0}\n'.format(e))


def initConfig():
    # output our log to stdout or syslog
    options.output = getConfig('output', 'stdout', options.configfile)
    options.sysloghostname = getConfig('sysloghostname', 'localhost', options.configfile)
    options.syslogport = getConfig('syslogport', 514, options.configfile)
    options.esservers = list(getConfig('esservers',
                                       'http://localhost:9200',
                                       options.configfile).split(','))

    # mongo connectivity options
    options.mongohost = getConfig('mongohost', 'localhost', options.configfile)
    options.mongoport = getConfig('mongoport', 3001, options.configfile)

    options.listen_host = getConfig('listen_host', '127.0.0.1', options.configfile)

    default_user_agent = 'Mozilla/5.0 (X11; Linux x86_64; rv:10.0) Gecko/20100101 Firefox/58.0'
    options.user_agent = getConfig('user_agent', default_user_agent, options.configfile)


parser = OptionParser()
parser.add_option(
    "-c",
    dest='configfile',
    default=__file__.replace(".py", ".conf"),
    help="configuration file to use")
(options, args) = parser.parse_args()
initConfig()
initLogger(options)
registerPlugins()

if __name__ == "__main__":
    run(host=options.listen_host, port=8081)
else:
    application = default_app()
