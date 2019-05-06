#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
# Copyright (c) 2017 Mozilla Corporation


import os
import json
import time

import pytest
from dateutil.parser import parse

from rest_test_suite import RestTestSuite


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
        title = dashboardjson['dashboard']['title']
        dashid = dash_name.replace(' ', '-')
        if dash_name:
            title = dash_name
        dashboardjson['dashboard']['title'] = dash_name
        return self.es_client.save_dashboard(dashboardjson, dash_name, doc_id=dashid)

    def teardown(self):
        super(TestKibanaDashboardsRoute, self).teardown()
        if pytest.config.option.delete_indexes:
            self.es_client.delete_index('.kibana', True)

    def setup(self):
        super(TestKibanaDashboardsRoute, self).setup()
        if pytest.config.option.delete_indexes:
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

            json_resp.sort()

            assert json_resp[1]['url'].endswith("/app/kibana#/dashboard/Example-SSH-Dashboard") is True
            assert json_resp[1]['name'] == 'Example SSH Dashboard'

            assert json_resp[0]['url'].endswith("/app/kibana#/dashboard/Example-FTP-Dashboard") is True
            assert json_resp[0]['name'] == 'Example FTP Dashboard'


class TestKibanaDashboardsRouteWithoutDashboards(RestTestSuite):
    routes = ['/kibanadashboards', '/kibanadashboards/']

    status_code = 200

    def setup(self):
        super(TestKibanaDashboardsRouteWithoutDashboards, self).setup()
        if pytest.config.option.delete_indexes:
            self.es_client.delete_index('.kibana', True)
            self.es_client.create_index('.kibana')
        time.sleep(0.2)

    def teardown(self):
        super(TestKibanaDashboardsRouteWithoutDashboards, self).teardown()
        if pytest.config.option.delete_indexes:
            self.es_client.delete_index('.kibana', True)

    def test_route_endpoints(self):
        for route in self.routes:
            response = self.response_per_route(route)
            json_resp = json.loads(response.body)

            assert response.status_code == self.status_code
            assert json_resp == []


class TestLoginCountsRoute(RestTestSuite):

    routes = ['/logincounts', '/logincounts/']
    status_code = 200

    def setup(self):
        super(TestLoginCountsRoute, self).setup()

        # ttesterson test events
        for count in range(10):
            timestamp = self.current_timestamp()
            event = {
                "receivedtimestamp": timestamp,
                "utctimestamp": timestamp,
                "tags": [
                    "auth0"
                ],
                "timestamp": timestamp,
                "category": "authentication",
                "summary": "Failed login from ttesterson@mozilla.com srcIP=1.1.1.1",
                "details": {
                    "username": "ttesterson@mozilla.com",
                    "type": "Failed Login",
                    "success": False,
                }
            }
            self.populate_test_event(event)
        for count in range(5):
            timestamp = self.current_timestamp()
            event = {
                "receivedtimestamp": timestamp,
                "utctimestamp": timestamp,
                "tags": [
                    "auth0"
                ],
                "timestamp": timestamp,
                "category": "authentication",
                "summary": "Success Login for ttesterson@mozilla.com srcIP=1.1.1.1",
                "details": {
                    "username": "ttesterson@mozilla.com",
                    "type": "Success Login",
                    "success": True,
                }
            }
            self.populate_test_event(event)

        # ttester test events
        for count in range(9):
            timestamp = self.current_timestamp()
            event = {
                "receivedtimestamp": timestamp,
                "utctimestamp": timestamp,
                "tags": [
                    "auth0"
                ],
                "timestamp": timestamp,
                "category": "authentication",
                "summary": "Failed Login from ttester@mozilla.com srcIP=1.1.1.1",
                "details": {
                    "username": "ttester@mozilla.com",
                    "type": "Failed Login",
                    "success": False,
                }
            }
            self.populate_test_event(event)
        for count in range(7):
            timestamp = self.current_timestamp()
            event = {
                "receivedtimestamp": timestamp,
                "utctimestamp": timestamp,
                "tags": [
                    "auth0"
                ],
                "timestamp": timestamp,
                "category": "authentication",
                "summary": "Success Login for ttester@mozilla.com srcIP=1.1.1.1",
                "details": {
                    "username": "ttester@mozilla.com",
                    "type": "Success Login",
                    "success": True,
                }
            }
            self.populate_test_event(event)

        # qwerty test events
        for count in range(8):
            timestamp = self.current_timestamp()
            event = {
                "receivedtimestamp": timestamp,
                "utctimestamp": timestamp,
                "tags": [
                    "auth0"
                ],
                "timestamp": timestamp,
                "category": "authentication",
                "summary": "Failed Login from qwerty@mozillafoundation.org srcIP=1.1.1.1",
                "details": {
                    "username": "qwerty@mozillafoundation.org",
                    "type": "Failed Login",
                    "success": False,
                }
            }
            self.populate_test_event(event)
        for count in range(3):
            timestamp = self.current_timestamp()
            event = {
                "receivedtimestamp": timestamp,
                "utctimestamp": timestamp,
                "tags": [
                    "auth0"
                ],
                "timestamp": timestamp,
                "category": "authentication",
                "summary": "Success Login for qwerty@mozillafoundation.org",
                "details": {
                    "username": "qwerty@mozillafoundation.org",
                    "type": "Success Login",
                    "success": True,
                }
            }
            self.populate_test_event(event)

        for count in range(3):
            timestamp = RestTestSuite.subtract_from_timestamp({'hours': 22})
            event = {
                "receivedtimestamp": timestamp,
                "utctimestamp": timestamp,
                "tags": [
                    "auth0"
                ],
                "timestamp": timestamp,
                "category": "authentication",
                "summary": "Success Login for qwerty@mozillafoundation.org",
                "details": {
                    "username": "qwerty@mozillafoundation.org",
                    "type": "Success Login",
                    "success": True,
                }
            }
            self.populate_test_event(event)

        self.refresh('events')

    def test_route_endpoints(self):
        for route in self.routes:
            response = self.response_per_route(route)
            json_resp = json.loads(response.body)

            assert response.status_code == self.status_code

            assert type(json_resp) == list
            assert len(json_resp) == 3

            json_resp.sort()

            assert json_resp[0].keys() == ['username', 'failures', 'begin', 'end', 'success']
            assert json_resp[0]['username'] == 'qwerty@mozillafoundation.org'
            assert json_resp[0]['failures'] == 8
            assert json_resp[0]['success'] == 3
            assert type(json_resp[0]['begin']) == unicode
            assert parse(json_resp[0]['begin']).tzname() == 'UTC'
            assert type(json_resp[0]['end']) == unicode
            assert parse(json_resp[0]['begin']).tzname() == 'UTC'

            assert json_resp[1].keys() == ['username', 'failures', 'begin', 'end', 'success']
            assert json_resp[1]['username'] == 'ttester@mozilla.com'
            assert json_resp[1]['failures'] == 9
            assert json_resp[1]['success'] == 7
            assert type(json_resp[1]['begin']) == unicode
            assert parse(json_resp[1]['begin']).tzname() == 'UTC'
            assert type(json_resp[1]['end']) == unicode
            assert parse(json_resp[1]['begin']).tzname() == 'UTC'

            assert json_resp[2].keys() == ['username', 'failures', 'begin', 'end', 'success']
            assert json_resp[2]['username'] == 'ttesterson@mozilla.com'
            assert json_resp[2]['failures'] == 10
            assert json_resp[2]['success'] == 5
            assert type(json_resp[2]['begin']) == unicode
            assert parse(json_resp[2]['begin']).tzname() == 'UTC'
            assert type(json_resp[2]['end']) == unicode
            assert parse(json_resp[2]['begin']).tzname() == 'UTC'

# Routes left need to have unit tests written for:
# @route('/veris')
# @route('/veris/')
# @post('/blockip', methods=['POST'])
# @post('/blockip/', methods=['POST'])
# @post('/ipwhois', methods=['POST'])
# @post('/ipwhois/', methods=['POST'])
# @post('/ipintel', methods=['POST'])
# @post('/ipintel/', methods=['POST'])
# @post('/ipdshieldquery', methods=['POST'])
# @post('/ipdshieldquery/', methods=['POST'])
# @route('/plugins', methods=['GET'])
# @route('/plugins/', methods=['GET'])
# @route('/plugins/<endpoint>', methods=['GET'])
# @post('/incident', methods=['POST'])
# @post('/incident/', methods=['POST'])
