from .positive_test_suite import PositiveTestSuite
from .negative_test_suite import NegativeTestSuite

from mozdef_util.query_models import TermMatch


class TestTermMatchPositiveTestSuite(PositiveTestSuite):
    def query_tests(self):
        tests = [
            [
                TermMatch('summary', 'test'), [
                    {'summary': 'test'},
                    {'summary': 'Test'},
                    {'summary': 'test summary'},
                    {'summary': 'example test summary'},
                    {'summary': 'example summary test'},
                ]
            ],
            [
                TermMatch('summary', 'ldap'), [
                    {'summary': 'LDAP'},
                    {'summary': 'lDaP'},
                    {'summary': 'ldap'},
                ]
            ],
            [
                TermMatch('summary', 'LDAP'), [
                    {'summary': 'LDAP'},
                    {'summary': 'lDaP'},
                    {'summary': 'ldap'},
                ]
            ],
            [
                TermMatch('summary', 'LDAP_INVALID_CREDENTIALS'), [
                    {'summary': 'LDaP_InVaLID_CREDeNTiALS'},
                ]
            ],
            [
                TermMatch('details.results', 'LDAP_INVALID_CREDENTIALS'), [
                    {
                        'details': {
                            "results": "LDAP_INVALID_CREDENTIALS",
                        }
                    }
                ]
            ],
            [
                TermMatch('hostname', 'hostname.domain.com'), [
                    {'hostname': 'hostname.domain.com'},
                ]
            ],
            [
                TermMatch('somekey', 'tag'), [
                    {'somekey': ['tag', 'other']},
                ]
            ],
        ]
        return tests


class TestTermMatchNegativeTestSuite(NegativeTestSuite):
    def query_tests(self):
        tests = [
            [
                TermMatch('details.resultss', 'ldap'), [
                    {
                        'details': {
                            "resultss": "LDAP",
                        }
                    }
                ]
            ],
            [
                TermMatch('summary', 'test'), [
                    {'summary': 'example summary'},
                    {'summary': 'example summary tes'},
                    {'summary': 'testing'},
                    {'summary': 'test.mozilla.domain'},
                    {'summary': 'mozilla.test.domain'},
                    {'summary': 'mozilla.test'},
                ]
            ],
            [
                TermMatch('note', 'test'), [
                    {'note': 'example note'},
                    {'note': 'example note tes'},
                    {'note': 'testing'},
                    {'summnoteary': 'test.mozilla.domain'},
                    {'note': 'mozilla.test.domain'},
                    {'note': 'mozilla.test'},
                ]
            ],
            [
                TermMatch('summary', 'sum'), [
                    {'summary': 'example test summary'},
                    {'summary': 'example summary'},
                    {'summary': 'summary test'},
                    {'summary': 'summary'},
                ]
            ],
            [
                TermMatch('hostname', 'hostname.domain.com'), [
                    {'hostname': 'sub.hostname.domain.com'},
                    {'hostname': 'hostnames.domain.com'},
                    {'hostname': 'domain.com'},
                    {'hostname': 'com'},
                ]
            ],
            [
                TermMatch('somekey', 'tag'), [
                    {'somekey': ['atag', 'tagging']},
                ]
            ],
        ]
        return tests
