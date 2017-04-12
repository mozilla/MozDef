from positive_test_suite import PositiveTestSuite
from negative_test_suite import NegativeTestSuite

import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), "../../lib"))
from query_models import TermMatch


class TestTermMatchPositiveTestSuite(PositiveTestSuite):
    def query_tests(self):
        tests = {
            TermMatch('summary', 'test'): [
                {'summary': 'test'},
                {'summary': 'Test'},
                {'summary': 'test summary'},
                {'summary': 'example test summary'},
                {'summary': 'example summary test'},
            ],

            TermMatch('summary', 'ldap'): [
                {'summary': 'LDAP'},
                {'summary': 'lDaP'},
                {'summary': 'ldap'},
            ],

            TermMatch('summary', 'LDAP'): [
                {'summary': 'LDAP'},
                {'summary': 'lDaP'},
                {'summary': 'ldap'},
            ],

            TermMatch('summary', 'LDAP_INVALID_CREDENTIALS'): [
                {'summary': 'LDaP_InVaLID_CREDeNTiALS'},
            ],

            TermMatch('details.results', 'LDAP_INVALID_CREDENTIALS'): [
                {
                    'details':
                    {
                        "results": "LDAP_INVALID_CREDENTIALS",
                    }
                }
            ],
            TermMatch('details.results', 'ldap'): [
                {
                    'details':
                    {
                        "results": "LDAP",
                    }
                }
            ],

            TermMatch('hostname', 'hostname.domain.com'): [
                {'hostname': 'hostname.domain.com'},
            ],
        }
        return tests


class TestTermMatchNegativeTestSuite(NegativeTestSuite):
    def query_tests(self):
        tests = {
            TermMatch('summary', 'test'): [
                {'summary': 'example summary'},
                {'summary': 'example summary tes'},
                {'summary': 'testing'},
                {'summary': 'test.mozilla.domain'},
                {'summary': 'mozilla.test.domain'},
                {'summary': 'mozilla.test'},
            ],
            TermMatch('summary', 'sum'): [
                {'summary': 'example test summary'},
                {'summary': 'example summary'},
                {'summary': 'summary test'},
                {'summary': 'summary'},
            ],
            TermMatch('hostname', 'hostname.domain.com'): [
                {'hostname': 'sub.hostname.domain.com'},
                {'hostname': 'hostnames.domain.com'},
                {'hostname': 'domain.com'},
            ],
        }
        return tests
