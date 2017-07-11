from positive_test_suite import PositiveTestSuite
from negative_test_suite import NegativeTestSuite

import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), "../../lib"))
from query_models import QueryStringMatch


hostname_test_regex = 'hostname: /(.*\.)*(sub|bus)+(\..*)*\.abc(\..*)*\.company\.com/'


class TestQueryStringMatchPositiveTestSuite(PositiveTestSuite):
    def query_tests(self):
        tests = {
            QueryStringMatch('summary: test'): [
                {'summary': 'test'},
            ],

            QueryStringMatch('summary: test conf'): [
                {'summary': 'test'},
                {'summary': 'conf'},
                {'summary': 'test conf'},
            ],

            QueryStringMatch(hostname_test_regex): [
                {'hostname': 'host1.sub.abc.company.com'},
                {'hostname': 'host1.sub.test.abc.company.com'},
                {'hostname': 'host1.sub.test.abc.domain.company.com'},
                {'hostname': 'host1.sub.abc.domain.company.com'},
                {'hostname': 'host2.bus.abc.domain.company.com'},
            ],
        }
        return tests


class TestQueryStringMatchNegativeTestSuite(NegativeTestSuite):
    def query_tests(self):
        tests = {
            QueryStringMatch('summary: test'): [
                {'summary': 'example summary'},
                {'summary': 'example summary tes'},
                {'summary': 'testing'},
                {'note': 'test'},
            ],

            QueryStringMatch('summary: test conf'): [
                {'summary': 'testing'},
                {'summary': 'configuration'},
                {'summary': 'testing configuration'},
            ],

            QueryStringMatch(hostname_test_regex): [
                {'hostname': 'host1.sub.abcd.company.com'},
                {'hostname': 'host1.sub.dabc.company.com'},
                {'hostname': 'host1.suba.abc.company.com'},
                {'hostname': 'host1.asub.abc.company.com'},
                {'hostname': 'host1.sub.dabc.domain.companyabc.com'},
                {'hostname': 'host2.bus.abc.domain.abcompany.com'},
            ],
        }
        return tests
