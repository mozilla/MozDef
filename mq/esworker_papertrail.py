#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
# Copyright (c) 2015 Mozilla Corporation

# Reads from papertrail using the API and inserts log data into ES in
# the same manner as esworker_eventtask.py


import json
import kombu
import sys
import socket
import time
from configlib import getConfig, OptionParser
from datetime import datetime, timedelta
import calendar
import requests

from mozdef_util.elasticsearch_client import ElasticsearchClient, ElasticsearchBadServer, ElasticsearchInvalidIndex, ElasticsearchException

from mozdef_util.utilities.toUTC import toUTC
from mozdef_util.utilities.to_unicode import toUnicode
from mozdef_util.utilities.remove_at import removeAt
from mozdef_util.utilities.is_cef import isCEF
from mozdef_util.utilities.logger import logger, initLogger

from lib.plugins import sendEventToPlugins, registerPlugins


# running under uwsgi?
try:
    import uwsgi
    hasUWSGI = True
except ImportError as e:
    hasUWSGI = False


class PTRequestor(object):

    def __init__(self, apikey, evmax=2000):
        self._papertrail_api = 'https://papertrailapp.com/api/v1/events/search.json'
        self._apikey = apikey
        self._events = {}
        self._evmax = evmax
        self._evidcache = []

    def parse_events(self, resp):
        for x in resp['events']:
            if x['id'] in self._evidcache:
                # saw this event last time, just ignore it
                continue
            self._events[x['id']] = x
        if 'reached_record_limit' in resp.keys() and resp['reached_record_limit']:
            return resp['min_id']
        return None

    def makerequest(self, query, stime, etime, maxid):
        payload = {
            'min_time': calendar.timegm(stime.utctimetuple()),
            'max_time': calendar.timegm(etime.utctimetuple()),
            'q': query
        }
        if maxid is not None:
            payload['max_id'] = maxid
        hdrs = {'X-Papertrail-Token': self._apikey}

        max_retries = 3
        total_retries = 0
        while True:
            logger.debug("Sending request to papertrail API")
            resp = requests.get(self._papertrail_api, headers=hdrs, params=payload)
            if resp.status_code == 200:
                break
            else:
                logger.debug("Received invalid status code: {0}: {1}".format(resp.status_code, resp.text))
                total_retries += 1
                if total_retries < max_retries:
                    logger.debug("Sleeping a bit then retrying")
                    time.sleep(2)
                else:
                    logger.error("Received too many error messages...exiting")
                    logger.error("Last malformed response: {0}: {1}".format(resp.status_code, resp.text))
                    sys.exit(1)

        return self.parse_events(resp.json())

    def request(self, query, stime, etime):
        self._events = {}
        maxid = None
        while True:
            maxid = self.makerequest(query, stime, etime, maxid)
            if maxid is None:
                break
            if len(self._events.keys()) > self._evmax:
                logger.warning('papertrail esworker hitting event request limit')
                break
        # cache event ids we return to allow for some duplicate filtering checks
        # during next run
        self._evidcache = self._events.keys()
        return self._events


def keyMapping(aDict):
    '''map common key/fields to a normalized structure,
       explicitly typed when possible to avoid schema changes for upsteam consumers
       Special accomodations made for logstash,nxlog, beaver, heka and CEF
       Some shippers attempt to conform to logstash-style @fieldname convention.
       This strips the leading at symbol since it breaks some elastic search
       libraries like elasticutils.
    '''
    returndict = dict()

    # uncomment to save the source event for debugging, or chain of custody/forensics
    # returndict['original']=aDict

    # set the timestamp when we received it, i.e. now
    returndict['receivedtimestamp'] = toUTC(datetime.now()).isoformat()
    returndict['mozdefhostname'] = options.mozdefhostname
    returndict['details'] = {}
    try:
        for k, v in aDict.iteritems():
            k = removeAt(k).lower()

            if k in ('message', 'summary'):
                returndict[u'summary'] = toUnicode(v)

            if k in ('payload') and 'summary' not in aDict.keys():
                # special case for heka if it sends payload as well as a summary, keep both but move payload to the details section.
                returndict[u'summary'] = toUnicode(v)
            elif k in ('payload'):
                returndict[u'details']['payload'] = toUnicode(v)

            if k in ('eventtime', 'timestamp', 'utctimestamp'):
                returndict[u'utctimestamp'] = toUTC(v).isoformat()
                returndict[u'timestamp'] = toUTC(v).isoformat()

            if k in ('hostname', 'source_host', 'host'):
                returndict[u'hostname'] = toUnicode(v)

            if k in ('tags'):
                if len(v) > 0:
                    returndict[u'tags'] = v

            # nxlog keeps the severity name in syslogseverity,everyone else should use severity or level.
            if k in ('syslogseverity', 'severity', 'severityvalue', 'level'):
                returndict[u'severity'] = toUnicode(v).upper()

            if k in ('facility', 'syslogfacility','source'):
                returndict[u'source'] = toUnicode(v)

            if k in ('pid', 'processid'):
                returndict[u'processid'] = toUnicode(v)

            # nxlog sets sourcename to the processname (i.e. sshd), everyone else should call it process name or pname
            if k in ('pname', 'processname', 'sourcename'):
                returndict[u'processname'] = toUnicode(v)

            # the file, or source
            if k in ('path', 'logger', 'file'):
                returndict[u'eventsource'] = toUnicode(v)

            if k in ('type', 'eventtype', 'category'):
                returndict[u'category'] = toUnicode(v)

            # custom fields as a list/array
            if k in ('fields', 'details'):
                if type(v) is not dict:
                    returndict[u'details'][u'message'] = v
                else:
                    if len(v) > 0:
                        for details_key, details_value in v.iteritems():
                            returndict[u'details'][details_key] = details_value

            # custom fields/details as a one off, not in an array
            # i.e. fields.something=value or details.something=value
            # move them to a dict for consistency in querying
            if k.startswith('fields.') or k.startswith('details.'):
                newName = k.replace('fields.', '')
                newName = newName.lower().replace('details.', '')
                # add field with a special case for shippers that
                # don't send details
                # in an array as int/floats/strings
                # we let them dictate the data type with field_datatype
                # convention
                if newName.endswith('_int'):
                    returndict[u'details'][unicode(newName)] = int(v)
                elif newName.endswith('_float'):
                    returndict[u'details'][unicode(newName)] = float(v)
                else:
                    returndict[u'details'][unicode(newName)] = toUnicode(v)

        # nxlog windows log handling
        if 'Domain' in aDict.keys() and 'SourceModuleType' in aDict.keys():
            # nxlog parses all windows event fields very well
            # copy all fields to details
            returndict[u'details'][k] = v

        if 'utctimestamp' not in returndict.keys():
            # default in case we don't find a reasonable timestamp
            returndict['utctimestamp'] = toUTC(datetime.now()).isoformat()

    except Exception as e:
        logger.exception('Received exception while normalizing message: %r' % e)
        logger.error('Malformed message: %r' % aDict)
        return None

    return returndict


def esConnect():
    '''open or re-open a connection to elastic search'''
    return ElasticsearchClient((list('{0}'.format(s) for s in options.esservers)), options.esbulksize)


class taskConsumer(object):

    def __init__(self, ptRequestor, esConnection):
        self.ptrequestor = ptRequestor
        self.esConnection = esConnection
        # calculate our initial request window
        self.lastRequestTime = toUTC(datetime.now()) - timedelta(seconds=options.ptinterval) - \
            timedelta(seconds=options.ptbackoff)

        if options.esbulksize != 0:
            # if we are bulk posting enable a timer to occasionally flush the bulker even if it's not full
            # to prevent events from sticking around an idle worker
            self.esConnection.start_bulk_timer()

    def run(self):
        while True:
            try:
                curRequestTime = toUTC(datetime.now()) - timedelta(seconds=options.ptbackoff)
                records = self.ptrequestor.request(options.ptquery, self.lastRequestTime, curRequestTime)
                # update last request time for the next request
                self.lastRequestTime = curRequestTime
                for msgid in records:
                    msgdict = records[msgid]

                    # strip any line feeds from the message itself, we just convert them
                    # into spaces
                    msgdict['message'] = msgdict['message'].replace('\n', ' ').replace('\r', '')

                    event = dict()
                    event['tags'] = ['papertrail', options.ptacctname]
                    event['details'] = msgdict

                    if 'generated_at' in event['details']:
                        event['utctimestamp'] = toUTC(event['details']['generated_at']).isoformat()
                    if 'hostname' in event['details']:
                        event['hostname'] = event['details']['hostname']
                    if 'message' in event['details']:
                        event['summary'] = event['details']['message']
                    if 'severity' in event['details']:
                        event['severity'] = event['details']['severity']
                    if 'source_ip' in event['details']:
                        event['sourceipaddress'] = event['details']['source_ip']
                    else:
                        event['severity'] = 'INFO'
                    event['category'] = 'syslog'

                    # process message
                    self.on_message(event, msgdict)

                time.sleep(options.ptinterval)

            except ValueError as e:
                logger.exception('Exception while handling message: %r' % e)

    def on_message(self, body, message):
        # print("RECEIVED MESSAGE: %r" % (body, ))
        try:
            # default elastic search metadata for an event
            metadata = {
                'index': 'events',
                'doc_type': 'event',
                'id': None
            }
            # just to be safe..check what we were sent.
            if isinstance(body, dict):
                bodyDict = body
            elif isinstance(body, str) or isinstance(body, unicode):
                try:
                    bodyDict = json.loads(body)   # lets assume it's json
                except ValueError as e:
                    # not json..ack but log the message
                    logger.error("esworker exception: unknown body type received %r" % body)
                    # message.ack()
                    return
            else:
                logger.error("esworker exception: unknown body type received %r" % body)
                # message.ack()
                return

            if 'customendpoint' in bodyDict.keys() and bodyDict['customendpoint']:
                # custom document
                # send to plugins to allow them to modify it if needed
                (normalizedDict, metadata) = sendEventToPlugins(bodyDict, metadata, pluginList)
            else:
                # normalize the dict
                # to the mozdef events standard
                normalizedDict = keyMapping(bodyDict)

                # send to plugins to allow them to modify it if needed
                if normalizedDict is not None and isinstance(normalizedDict, dict) and normalizedDict.keys():
                    (normalizedDict, metadata) = sendEventToPlugins(normalizedDict, metadata, pluginList)

            # drop the message if a plug in set it to None
            # signaling a discard
            if normalizedDict is None:
                # message.ack()
                return

            # make a json version for posting to elastic search
            jbody = json.JSONEncoder().encode(normalizedDict)

            if isCEF(normalizedDict):
                # cef records are set to the 'deviceproduct' field value.
                metadata['doc_type'] = 'cef'
                if 'details' in normalizedDict.keys() and 'deviceproduct' in normalizedDict['details'].keys():
                    # don't create strange doc types..
                    if ' ' not in normalizedDict['details']['deviceproduct'] and '.' not in normalizedDict['details']['deviceproduct']:
                        metadata['doc_type'] = normalizedDict['details']['deviceproduct']

            try:
                bulk = False
                if options.esbulksize != 0:
                    bulk = True

                self.esConnection.save_event(
                    index=metadata['index'],
                    doc_id=metadata['id'],
                    doc_type=metadata['doc_type'],
                    body=jbody,
                    bulk=bulk
                )

            except (ElasticsearchBadServer, ElasticsearchInvalidIndex) as e:
                # handle loss of server or race condition with index rotation/creation/aliasing
                try:
                    self.esConnection = esConnect()
                    # message.requeue()
                    return
                except kombu.exceptions.MessageStateError:
                    # state may be already set.
                    return
            except ElasticsearchException as e:
                # exception target for queue capacity issues reported by elastic search so catch the error, report it and retry the message
                try:
                    logger.exception('ElasticSearchException: {0} reported while indexing event'.format(e))
                    # message.requeue()
                    return
                except kombu.exceptions.MessageStateError:
                    # state may be already set.
                    return

            # message.ack()
        except Exception as e:
            logger.exception(e)
            logger.error('Malformed message body: %r' % body)


def main():
    if hasUWSGI:
        logger.info("started as uwsgi mule {0}".format(uwsgi.mule_id()))
    else:
        logger.info('started without uwsgi')

    # establish api interface with papertrail
    ptRequestor = PTRequestor(options.ptapikey, evmax=options.ptquerymax)

    # consume our queue
    taskConsumer(ptRequestor, es).run()


def initConfig():
    # capture the hostname
    options.mozdefhostname = getConfig('mozdefhostname', socket.gethostname(), options.configfile)

    # elastic search options. set esbulksize to a non-zero value to enable bulk posting, set timeout to post no matter how many events after X seconds.
    options.esservers = list(getConfig('esservers', 'http://localhost:9200', options.configfile).split(','))
    options.esbulksize = getConfig('esbulksize', 0, options.configfile)
    options.esbulktimeout = getConfig('esbulktimeout', 30, options.configfile)

    # papertrail configuration
    options.ptapikey = getConfig('papertrailapikey', 'none', options.configfile)
    options.ptquery = getConfig('papertrailquery', '', options.configfile)
    options.ptinterval = getConfig('papertrailinterval', 60, options.configfile)
    options.ptbackoff = getConfig('papertrailbackoff', 300, options.configfile)
    options.ptacctname = getConfig('papertrailaccount', 'unset', options.configfile)
    options.ptquerymax = getConfig('papertrailmaxevents', 2000, options.configfile)

    # plugin options
    # secs to pass before checking for new/updated plugins
    # seems to cause memory leaks..
    # regular updates are disabled for now,
    # though we set the frequency anyway.
    options.plugincheckfrequency = getConfig('plugincheckfrequency', 120, options.configfile)


if __name__ == '__main__':
    # configure ourselves
    parser = OptionParser()
    parser.add_option("-c", dest='configfile', default=sys.argv[0].replace('.py', '.conf'), help="configuration file to use")
    (options, args) = parser.parse_args()
    initConfig()
    initLogger(options)

    # open ES connection globally so we don't waste time opening it per message
    es = esConnect()

    pluginList = registerPlugins()

    try:
        main()
    except KeyboardInterrupt as e:
        logger.info("Exiting worker")
        if options.esbulksize != 0:
            es.finish_bulk()
    except Exception as e:
        if options.esbulksize != 0:
            es.finish_bulk()
        raise
