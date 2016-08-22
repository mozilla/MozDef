import os
import json

from get_method_test_suite import GetMethodTestSuite


class TestTestRoute(GetMethodTestSuite):
    routes = ['/test', '/test/']

    status_code = 200
    body = ''


class TestStatusRoute(GetMethodTestSuite):
    routes = ['/status', '/status/']

    status_code = 200
    body = '{"status": "ok"}'


class TestKibanaDashboardsRoute(GetMethodTestSuite):
    routes = ['/kibanadashboards', '/kibanadashboards/']

    status_code = 200

    def setup(self):
        super(TestKibanaDashboardsRoute, self).setup()

        self.es_client.delete_index('kibana-int', True)
        json_dashboard_location = os.path.join(os.path.dirname(__file__), "ssh_dashboard.json")
        self.es_client.save_dashboard(json_dashboard_location, "Example SSH Dashboard")
        self.es_client.save_dashboard(json_dashboard_location, "Example FTP Dashboard")
        self.es_client.flush('kibana-int')

    def test_route_endpoints(self):
        for route in self.routes:
            response = self.response_per_route(route)
            json_resp = json.loads(response.body)

            assert response.status_code == self.status_code

            assert type(json_resp) == list
            assert len(json_resp) == 2

            json_resp.sort()

            assert json_resp[1]['url'].endswith(
                ":9090/index.html#/dashboard/elasticsearch/Example SSH Dashboard") is True
            assert json_resp[1]['name'] == 'Example SSH Dashboard'

            assert json_resp[0]['url'].endswith(
                ":9090/index.html#/dashboard/elasticsearch/Example FTP Dashboard") is True
            assert json_resp[0]['name'] == 'Example FTP Dashboard'


# Routes left need to have unit tests written for:
# @route('/ldapLogins')
# @route('/ldapLogins/')
# @route('/veris')
# @route('/veris/')
# @post('/blockip', methods=['POST'])
# @post('/blockip/', methods=['POST'])
# @post('/ipwhois', methods=['POST'])
# @post('/ipwhois/', methods=['POST'])
# @post('/ipintel', methods=['POST'])
# @post('/ipintel/', methods=['POST'])
# @post('/ipcifquery', methods=['POST'])
# @post('/ipcifquery/', methods=['POST'])
# @post('/ipdshieldquery', methods=['POST'])
# @post('/ipdshieldquery/', methods=['POST'])
# @route('/plugins', methods=['GET'])
# @route('/plugins/', methods=['GET'])
# @route('/plugins/<endpoint>', methods=['GET'])
# @post('/incident', methods=['POST'])
# @post('/incident/', methods=['POST'])
