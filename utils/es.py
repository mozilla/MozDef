#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
# Copyright (c) 2014 Mozilla Corporation
#
# Contributors:
# Anthony Verez averez@mozilla.com

import pyes
import json
import requests
from datetime import datetime

class Elasticsearch(object):
    def __init__(self, esserver):
        """
        Class used for ES features not supported by pyes
        and for shortcuts when using pyes
        """
        self.esserver = esserver
        self.conn = pyes.ES(esserver)

    def deleteIndex(self, index):
        print('Deleting %s index...' % index)
        try:
            self.conn.indices.delete_index(index)
        except:
            pass

    def setupIndexTemplate(self, template_name, template_file):
        f = open(template_file)
        templateData = f.read()
        url = '{0}/_template/{1}'.format(self.esserver, template_name)
        r = requests.put(url=url, data=templateData)
        if r.status_code == 200:
            print('Successfully put %s template' % template_name)
        else:
            print('Problem putting %s template %r' % (template_name, r))
        f.close()

    def createIndex(self, index):
        print('Creating %s index...' % index)
        try:
            self.conn.indices.create_index(index)
        except:
            pass

    def loadDocs(self, index, docs_type, docs_file, update_date=False):
        print('Loading docs from %s...' % docs_file)
        f = open(docs_file)
        data = json.load(f)
        for l in data:
            if update_date:
                # update date to right now
                l['utctimestamp'] = datetime.utcnow().isoformat()+'+00:00'
            self.conn.index(l, index, docs_type)
        f.close()

    def loadDashboard(self, dash_name, dash_file):
        print('Loading %s dashboard...' % dash_name)

        f = open(dash_file)
        dashboardjson = json.load(f)
        url = '{0}/kibana-int/dashboard/{1}'.format(
            self.esserver,
            dashboardjson['title'])
        dashboarddata = {
            "user": "guest",
            "group": "guest",
            "title": dashboardjson['title'],
            "dashboard": json.dumps(dashboardjson)
        }
        r = requests.put(url=url, data=json.dumps(dashboarddata))
        if r.status_code < 220:
            print('Successfully put %s kibana dashboard' % dash_name)
        else:
            print(r.json())
            print('Problem putting %s kibana dashboard %r' % (dash_name, r))
        f.close()
