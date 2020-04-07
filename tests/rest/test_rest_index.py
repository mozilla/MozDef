#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# Copyright (c) 2017 Mozilla Corporation


import os
import json
import time

from operator import itemgetter

from .rest_test_suite import RestTestSuite


class TestMongoConnection(RestTestSuite):
    routes = ['/test', '/test/']
    status_code = 200

    def setup(self):
        super().setup()
        self.mongoclient.test_database.tests.insert_one({
            'name': 'test_item_1',
            'value': 32
        })

    def teardown(self):
        super().teardown()
        self.mongoclient.test_database.tests.delete_one({
            'name': 'test_item_1'
        })

    def test_route_endpoints(self):
        db = self.mongoclient.test_database

        db.tests.update_one(
            {'name': 'test_item_1'},
            {'$inc': {'value': 32}})

        found = db.tests.find_one({'name': 'test_item_1'})

        assert found.get('value') == 64


class TestTestRoute(RestTestSuite):
    routes = ['/test', '/test/']

    status_code = 200
    body = ''


class TestStatusRoute(RestTestSuite):
    routes = ['/status', '/status/']

    status_code = 200
    body = '{"status": "ok", "service": "restapi"}'


class TestKibanaDashboardsRoute(RestTestSuite):
    routes = ['/kibanadashboards', '/kibanadashboards/']

    status_code = 200

    def save_dashboard(self, dash_file, dash_name):
        f = open(dash_file)
        dashboardjson = json.load(f)
        f.close()
        dashid = dash_name.replace(' ', '-')
        dashid = 'dashboard:{0}'.format(dashid)
        dashboardjson['dashboard']['title'] = dash_name
        dashboardjson['type'] = 'dashboard'
        return self.es_client.save_object(body=dashboardjson, index='.kibana', doc_id=dashid)

    def teardown(self):
        super().teardown()
        if self.config_delete_indexes:
            self.es_client.delete_index('.kibana', True)

    def setup(self):
        super().setup()
        if self.config_delete_indexes:
            self.es_client.delete_index('.kibana', True)
            self.es_client.create_index('.kibana')

        json_dashboard_location = os.path.join(os.path.dirname(__file__), "ssh_dashboard.json")
        self.save_dashboard(json_dashboard_location, "Example SSH Dashboard")
        self.save_dashboard(json_dashboard_location, "Example FTP Dashboard")
        self.refresh('.kibana')

    def test_route_endpoints(self):
        for route in self.routes:
            response = self.response_per_route(route)
            json_resp = json.loads(response.body)

            assert response.status_code == self.status_code

            assert type(json_resp) == list
            assert len(json_resp) == 2

            sorted_dashboards = sorted(json_resp, key=itemgetter('name'))
            assert sorted_dashboards[0]['id'] == "Example-FTP-Dashboard"
            assert sorted_dashboards[0]['name'] == 'Example FTP Dashboard'
            assert sorted_dashboards[1]['id'] == "Example-SSH-Dashboard"
            assert sorted_dashboards[1]['name'] == 'Example SSH Dashboard'


class TestKibanaDashboardsRouteWithoutDashboards(RestTestSuite):
    routes = ['/kibanadashboards', '/kibanadashboards/']

    status_code = 200

    def setup(self):
        super().setup()
        if self.config_delete_indexes:
            self.es_client.delete_index('.kibana', True)
            self.es_client.create_index('.kibana')
        time.sleep(0.2)

    def teardown(self):
        super().teardown()
        if self.config_delete_indexes:
            self.es_client.delete_index('.kibana', True)

    def test_route_endpoints(self):
        for route in self.routes:
            response = self.response_per_route(route)
            json_resp = json.loads(response.body)

            assert response.status_code == self.status_code
            assert json_resp == []

# Routes left need to have unit tests written for:
# @route('/veris')
# @route('/veris/')
# @post('/blockip', methods=['POST'])
# @post('/blockip/', methods=['POST'])
# @post('/ipwhois', methods=['POST'])
# @post('/ipwhois/', methods=['POST'])
# @post('/ipdshieldquery', methods=['POST'])
# @post('/ipdshieldquery/', methods=['POST'])
# @route('/plugins', methods=['GET'])
# @route('/plugins/', methods=['GET'])
# @route('/plugins/<endpoint>', methods=['GET'])
# @post('/incident', methods=['POST'])
# @post('/incident/', methods=['POST'])
