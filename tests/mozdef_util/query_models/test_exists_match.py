from .positive_test_suite import PositiveTestSuite
from .negative_test_suite import NegativeTestSuite

from mozdef_util.query_models import ExistsMatch


class TestExistsMatchPositiveTestSuite(PositiveTestSuite):
    def query_tests(self):
        tests = [
            [
                ExistsMatch('summary'), [
                    {'summary': 'test'},
                    {'summary': 'example test summary'},
                ]
            ],
            [
                ExistsMatch('details.note'), [
                    {
                        'summary': 'garbage summary',
                        'details': {
                            'note': 'test'
                        }
                    },
                ]
            ]
        ]
        return tests


class TestExistsMatchNegativeTestSuite(NegativeTestSuite):
    def query_tests(self):
        tests = [
            [
                ExistsMatch('summary'), [
                    {'note': 'example note'},
                    {'sum': 'example sum'},
                    {'details': {'note': 'example note'}},
                ]
            ],
            [
                ExistsMatch('details.note'), [
                    {'summary': 'garbage summary','details': {'ipaddress': 'test'}},
                ]
            ]
        ]
        return tests
