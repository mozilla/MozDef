from positive_test_suite import PositiveTestSuite
from negative_test_suite import NegativeTestSuite

import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), "../../lib"))
from query_models import QueryStringMatch


hostname_test_regex = 'hostname: /(.*\.)*(groupa|groupb)\.(.*\.)*subdomain\.(.*\.)*.*/'


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
                {'hostname': 'host.groupa.test.def.subdomain.company.com'},
                {'hostname': 'host.groupa.test.def.subdomain.company.com'},
                {'hostname': 'host.groupa.subdomain.domain.company.com'},
                {'hostname': 'host.groupa.subdomain.domain1.company.com'},
                {'hostname': 'host.groupa.subdomain.company.com'},
                {'hostname': 'host1.groupa.subdomain.company.com'},
                {'hostname': 'host1.groupa.test.subdomain.company.com'},
                {'hostname': 'host-1.groupa.test.subdomain.domain.company.com'},
                {'hostname': 'host-v2-test6.groupa.test.subdomain.domain.company.com'},
                {'hostname': 'host1.groupa.subdomain.domain.company.com'},
                {'hostname': 'someotherhost1.hgi.groupa.subdomain.domain1.company.com'},
                {'hostname': 'host2.groupb.subdomain.domain.company.com'},
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
                {'hostname': ''},
                {'hostname': 'host.subdomain.company.com'},
                {'hostname': 'host.subdomain.domain1.company.com'},
                {'hostname': 'groupa.abc.company.com'},
                {'hostname': 'asub.subdomain.company.com'},
                {'hostname': 'example.com'},
                {'hostname': 'abc.company.com'},
                {'hostname': 'host1.groupa.asubdomain.company.com'},
                {'hostname': 'host1.groupa.subdomaina.company.com'},
                {'hostname': 'host1.groupaa.subdomain.company.com'},
                {'hostname': 'host1.agroupb.subdomain.company.com'},
            ],
        }
        return tests
