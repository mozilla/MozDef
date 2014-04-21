#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
# Copyright (c) 2014 Mozilla Corporation
#
# Contributors:
# Anthony Verez averez@mozilla.com

import json
import pyes
import sys
import requests
from configlib import getConfig, OptionParser


def deleteIndices(conn):
    print('Deleting alerts and events indices...')
    try:
        conn.indices.delete_index("alerts")
        conn.indices.delete_index("events")
    except:
        pass


def setupTemplates(options):
    f = open('events_template.json')
    eventsTemplate = f.read()
    url = '{0}/_template/eventstemplate'.format(options.esservers[0])
    r = requests.put(url=url, data=eventsTemplate)
    if r.status_code == 200:
        print('Successfully put events template')
    else:
        print('Problem putting events template %r' % r)
    f.close()

    f = open('alerts_template.json')
    alertsTemplate = f.read()
    url = '{0}/_template/alertstemplate'.format(options.esservers[0])
    r = requests.put(url=url, data=alertsTemplate)
    if r.status_code == 200:
        print('Successfully put alerts template')
    else:
        print('Problem putting alerts template %r' % r)
    f.close()


def createIndices(conn):
    print('Creating alerts and events indices...')
    try:
        conn.indices.create_index("alerts")
        conn.indices.delete_index("events")
    except:
        pass


def loadDocs(conn):
    print('Loading sample docs...')
    f = open('alerts.json')
    data = json.load(f)
    for l in data:
        conn.index(l, "alerts", "alert")
    f.close()

    f = open('events-auditd.json')
    data = json.load(f)
    for l in data:
        conn.index(l, "events", "auditd")
    f.close()

    f = open('events-event.json')
    data = json.load(f)
    for l in data:
        conn.index(l, "events", "event")
    f.close()

    f = open('events-cloudtrail.json')
    data = json.load(f)
    for l in data:
        conn.index(l, "events", "cloudtrail")
    f.close()


def loadDashboards(conn):
    print('Loading sample dashboards...')

    f = open('events-kibana.json')
    dashboardjson = json.load(f)
    url = '{0}/kibana-int/dashboard/{1}'.format(
        options.esservers[0],
        dashboardjson['title'])
    dashboarddata = {
        "user": "guest",
        "group": "guest",
        "title": dashboardjson['title'],
        "dashboard": json.dumps(dashboardjson)
    }
    r = requests.put(url=url, data=json.dumps(dashboarddata))
    if r.status_code < 220:
        print('Successfully put events kibana dashboard')
    else:
        print r.json()
        print('Problem putting events kibana dashboard %r' % r)
    f.close()

    f = open('alerts-kibana.json')
    dashboardjson = json.load(f)
    url = '{0}/kibana-int/dashboard/{1}'.format(
        options.esservers[0],
        dashboardjson['title'])
    dashboarddata = {
        "user": "guest",
        "group": "guest",
        "title": dashboardjson['title'],
        "dashboard": json.dumps(dashboardjson)
    }
    r = requests.put(url=url, data=json.dumps(dashboarddata))
    if r.status_code < 220:
        print('Successfully put alerts kibana dashboard')
    else:
        print r.json()
        print('Problem putting alerts kibana dashboard %r' % r)
    f.close()


def initConfig():
    options.esservers = list(getConfig(
        'esservers',
        'http://localhost:9200',
        options.configfile).split(',')
    )


if __name__ == '__main__':
    parser = OptionParser()
    parser.add_option("-c",
                      dest='configfile',
                      default=sys.argv[0].replace('.py', '.conf'),
                      help="configuration file to use")
    (options, args) = parser.parse_args()
    initConfig()
    conn = pyes.ES(options.esservers[0])
    deleteIndices(conn)
    setupTemplates(options)
    createIndices(conn)
    loadDocs(conn)
    loadDashboards(conn)
