#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# Copyright (c) 2017 Mozilla Corporation


from datetime import datetime
import json
import os
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


class TestAlertStatus(RestTestSuite):
    def setup(self):
        super().setup()

        # Testing both routes is superfluous.
        self.route = '/alertstatus'
        self.alert_id = 'testid123'

        test_alert = {
            'esmetadata': {
                'id': self.alert_id
            },
            'status': 'manual'
        }

        self.alerts_db = self.mongoclient.meteor.alerts
        self.alerts_db.insert_one(test_alert)

    def teardown(self):
        super().teardown()

        self.alerts_db.delete_one({'esmetadata': {'id': self.alert_id}})

    def test_route_endpoints(self):
        req_params = {
            'alert': self.alert_id,
            'status': 'acknowledged',
            'user': {
                'email': 'tester@testing.com',
                'slack': 'tester'
            },
            'identityConfidence': 'high',
            'response': 'yes'
        }

        resp = self.app.post_json(self.route, req_params)

        query = {'esmetadata.id': self.alert_id}
        alert = self.alerts_db.find_one(query)

        assert 'error' in resp.json
        assert resp.json['error'] is None

        assert alert['status'] == 'acknowledged'
        assert alert['details']['triage']['user']['slack'] == 'tester'
        assert alert['details']['triage']['response'] == 'yes'
        assert 'acknowledged' in alert
        assert alert['acknowledgedby'] == 'triagebot'

        return


class TestRetrieveDuplicateChain(RestTestSuite):
    def setup(self):
        super().setup()

        self.route = "/alerttriagechain"
        self.alert_label = "test_alert_label"
        self.alert_id = "testid4321"
        self.user_email = "tester@mozilla.com"

        self.chains_db = self.mongoclient.meteor["duplicatechains"]

        self.chains_db.delete_many({"user": self.user_email})

        self.chains_db.insert_one({
            "alert": self.alert_label,
            "user": self.user_email,
            "identifiers": [self.alert_id],
            "created": datetime.utcnow(),
            "modified": datetime.utcnow(),
        })

    def teardown(self):
        super().setup()

        self.chains_db.delete_one({
            "alert": self.alert_label,
            "user": self.user_email,
        })

    def test_route_endpoints(self):
        req_params = {
            "alert": self.alert_label,
            "user": self.user_email,
        }

        resp = self.app.get(self.route, req_params)

        assert "error" in resp.json
        assert resp.json["error"] is None
        assert "identifiers" in resp.json
        assert len(resp.json["identifiers"]) == 1
        assert resp.json["identifiers"][0] == self.alert_id
        assert "created" in resp.json
        assert "modified" in resp.json


class TestCreateDuplicateChain(RestTestSuite):
    def setup(self):
        super().setup()

        self.route = '/alerttriagechain'
        self.alert_label = 'test_alert_label'
        self.alert_id = 'testid1234'
        self.user_email = 'tester@mozilla.com'

        self.chains_db = self.mongoclient.meteor['duplicatechains']

        self.chains_db.delete_many({"user": self.user_email})

    def teardown(self):
        super().teardown()

        self.chains_db.delete_one({
            "alert": self.alert_label,
            "user": self.user_email,
        })

    def test_route_endpoints(self):
        req_params = {
            'alert': self.alert_label,
            'user': self.user_email,
            'identifiers': [self.alert_id]
        }

        resp = self.app.post_json(self.route, req_params)

        query = {'alert': self.alert_label, 'user': self.user_email}
        chain = self.chains_db.find_one(query)

        assert 'error' in resp.json
        assert resp.json['error'] is None

        assert len(chain['identifiers']) == 1
        assert chain['identifiers'][0] == self.alert_id
        assert "created" in chain
        assert "modified" in chain


class TestUpdateDuplicateChain(RestTestSuite):
    def setup(self):
        super().setup()

        self.route = "/alerttriagechain"
        self.alert_label = "test_alert_label"
        self.alert_id = "testid12"
        self.new_id = "testid21"
        self.user_email = "tester@mozilla.com"

        self.chains_db = self.mongoclient.meteor["duplicatechains"]

        self.chains_db.delete_many({"user": self.user_email})

        self.created = datetime.utcnow()

        self.chains_db.insert_one({
            "alert": self.alert_label,
            "user": self.user_email,
            "identifiers": [self.alert_id],
            "created": self.created,
            "modified": self.created,
        })

    def teardown(self):
        super().teardown()

        self.chains_db.delete_one({
            "alert": self.alert_label,
            "user": self.user_email,
        })

    def test_route_endpoints(self):
        req_params = {
            "alert": self.alert_label,
            "user": self.user_email,
            "identifiers": [self.new_id],
        }

        resp = self.app.put_json(self.route, req_params)

        query = {"alert": self.alert_label, "user": self.user_email}
        chain = self.chains_db.find_one(query)

        assert "error" in resp.json
        assert resp.json["error"] is None

        assert len(chain["identifiers"]) == 2
        assert self.alert_id in chain["identifiers"]
        assert self.new_id in chain["identifiers"]
        assert chain["modified"] != self.created


class TestDeleteDuplicateChain(RestTestSuite):
    def setup(self):
        super().setup()

        self.route = "/alerttriagechain"
        self.alert_label = "test_alert_label"
        self.alert_id = "test312"
        self.user_email = "tester@mozilla.com"

        self.chains_db = self.mongoclient.meteor["duplicatechains"]

        self.chains_db.delete_many({"user": self.user_email})

        self.chains_db.insert_one({
            "alert": self.alert_label,
            "user": self.user_email,
            "identifiers": [self.alert_id],
            "created": datetime.utcnow(),
            "modified": datetime.utcnow(),
        })

    def test_route_endpoints(self):
        req_params = {
            "alert": self.alert_label,
            "user": self.user_email,
        }

        resp = self.app.delete_json(self.route, req_params)

        chain = self.chains_db.find_one(req_params)

        assert "error" in resp.json
        assert resp.json["error"] is None

        assert chain is None  # Should no longer find the deleted chain

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
