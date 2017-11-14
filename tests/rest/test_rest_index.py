#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
# Copyright (c) 2017 Mozilla Corporation
#
# Contributors:
# Brandon Myers bmyers@mozilla.com
# Alicia Smith asmith@mozilla.com


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
    body = '{"status": "ok"}'


class TestKibanaDashboardsRoute(RestTestSuite):
    routes = ['/kibanadashboards', '/kibanadashboards/']

    status_code = 200

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
        self.es_client.save_dashboard(json_dashboard_location, "Example SSH Dashboard")
        self.es_client.save_dashboard(json_dashboard_location, "Example FTP Dashboard")
        self.flush('.kibana')

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


class TestLdapLoginsRoute(RestTestSuite):

    routes = ['/ldapLogins', '/ldapLogins/']
    status_code = 200

    def setup(self):
        super(TestLdapLoginsRoute, self).setup()

        # ttesterson test events
        for count in range(10):
            timestamp = self.current_timestamp()
            event = {
                "receivedtimestamp": timestamp,
                "utctimestamp": timestamp,
                "tags": [
                    "ldap"
                ],
                "timestamp": timestamp,
                "summary": "LDAP_INVALID_CREDENTIALS ttesterson@mozilla.com,o=com,dc=mozilla srcIP=1.1.1.1",
                "details": {
                    "dn": "ttesterson@mozilla.com,o=com,dc=mozilla",
                    "result": "LDAP_INVALID_CREDENTIALS",
                }
            }
            self.populate_test_event(event)
        for count in range(5):
            timestamp = self.current_timestamp()
            event = {
                "receivedtimestamp": timestamp,
                "utctimestamp": timestamp,
                "tags": [
                    "ldap"
                ],
                "timestamp": timestamp,
                "summary": "LDAP_SUCCESS ttesterson@mozilla.com,o=com,dc=mozilla srcIP=1.1.1.1",
                "details": {
                    "dn": "ttesterson@mozilla.com,o=com,dc=mozilla",
                    "result": "LDAP_SUCCESS",
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
                    "ldap"
                ],
                "timestamp": timestamp,
                "summary": "LDAP_INVALID_CREDENTIALS ttester@mozilla.com,o=com,dc=mozilla srcIP=1.1.1.1",
                "details": {
                    "dn": "ttester@mozilla.com,o=com,dc=mozilla",
                    "result": "LDAP_INVALID_CREDENTIALS",
                }
            }
            self.populate_test_event(event)
        for count in range(7):
            timestamp = self.current_timestamp()
            event = {
                "receivedtimestamp": timestamp,
                "utctimestamp": timestamp,
                "tags": [
                    "ldap"
                ],
                "timestamp": timestamp,
                "summary": "LDAP_SUCCESS ttester@mozilla.com,o=com,dc=mozilla srcIP=1.1.1.1",
                "details": {
                    "dn": "ttester@mozilla.com,o=com,dc=mozilla",
                    "result": "LDAP_SUCCESS",
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
                    "ldap"
                ],
                "timestamp": timestamp,
                "summary": "LDAP_INVALID_CREDENTIALS qwerty@mozillafoundation.org,o=org,dc=mozillafoundation srcIP=1.1.1.1",
                "details": {
                    "dn": "qwerty@mozillafoundation.org,o=org,dc=mozillafoundation",
                    "result": "LDAP_INVALID_CREDENTIALS",
                }
            }
            self.populate_test_event(event)
        for count in range(3):
            timestamp = self.current_timestamp()
            event = {
                "receivedtimestamp": timestamp,
                "utctimestamp": timestamp,
                "tags": [
                    "ldap"
                ],
                "timestamp": timestamp,
                "summary": "LDAP_SUCCESS qwerty@mozillafoundation.org,o=org,dc=mozillafoundation",
                "details": {
                    "dn": "qwerty@mozillafoundation.org,o=org,dc=mozillafoundation",
                    "result": "LDAP_SUCCESS",
                }
            }
            self.populate_test_event(event)

        for count in range(3):
            timestamp = RestTestSuite.subtract_from_timestamp({'hours': 2})
            event = {
                "receivedtimestamp": timestamp,
                "utctimestamp": timestamp,
                "tags": [
                    "ldap"
                ],
                "timestamp": timestamp,
                "summary": "LDAP_SUCCESS qwerty@mozillafoundation.org,o=org,dc=mozillafoundation",
                "details": {
                    "dn": "qwerty@mozillafoundation.org,o=org,dc=mozillafoundation",
                    "result": "LDAP_SUCCESS",
                }
            }
            self.populate_test_event(event)

        self.flush('events')

    def test_route_endpoints(self):
        for route in self.routes:
            response = self.response_per_route(route)
            json_resp = json.loads(response.body)

            assert response.status_code == self.status_code

            assert type(json_resp) == list
            assert len(json_resp) == 3

            json_resp.sort()

            assert json_resp[0].keys() == ['dn', 'failures', 'begin', 'end', 'success']
            assert json_resp[0]['dn'] == 'qwerty@mozillafoundation.org,o=org,dc=mozillafoundation'
            assert json_resp[0]['failures'] == 8
            assert json_resp[0]['success'] == 3
            assert type(json_resp[0]['begin']) == unicode
            assert parse(json_resp[0]['begin']).tzname() == 'UTC'
            assert type(json_resp[0]['end']) == unicode
            assert parse(json_resp[0]['begin']).tzname() == 'UTC'

            assert json_resp[1].keys() == ['dn', 'failures', 'begin', 'end', 'success']
            assert json_resp[1]['dn'] == 'ttester@mozilla.com,o=com,dc=mozilla'
            assert json_resp[1]['failures'] == 9
            assert json_resp[1]['success'] == 7
            assert type(json_resp[1]['begin']) == unicode
            assert parse(json_resp[1]['begin']).tzname() == 'UTC'
            assert type(json_resp[1]['end']) == unicode
            assert parse(json_resp[1]['begin']).tzname() == 'UTC'

            assert json_resp[2].keys() == ['dn', 'failures', 'begin', 'end', 'success']
            assert json_resp[2]['dn'] == 'ttesterson@mozilla.com,o=com,dc=mozilla'
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
