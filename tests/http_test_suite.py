from webtest import TestApp

from tests.unit_test_suite import UnitTestSuite


class HTTPTestSuite(UnitTestSuite):

    def setup(self):
        self.app = TestApp(self.application)
        super().setup()

    def response_per_route(self, route):
        return self.app.get(route)

    def test_route_endpoints(self):
        for route in self.routes:
            response = self.response_per_route(route)
            assert response.status_code == self.status_code
            assert response.text == self.body
