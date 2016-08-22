from rest_test_suite import RestTestSuite


class GetMethodTestSuite(RestTestSuite):

    def response_per_route(self, route):
        return self.app.get(route)

    def test_route_endpoints(self):
        for route in self.routes:
            response = self.response_per_route(route)
            assert response.status_code == self.status_code
            assert response.body == self.body
