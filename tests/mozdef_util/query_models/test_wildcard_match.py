from .positive_test_suite import PositiveTestSuite
from .negative_test_suite import NegativeTestSuite

from mozdef_util.query_models import WildcardMatch


class TestWildcardMatchPositiveTestSuite(PositiveTestSuite):
    def query_tests(self):
        tests = [
            [
                WildcardMatch('summary', 'te*'), [
                    {'summary': 'test'},
                    {'summary': 'test summary'},
                    {'summary': 'example test summary'},
                    {'summary': 'example summary test'},
                ]
            ],
            [
                WildcardMatch('summary', '*te*'), [
                    {'summary': 'abcteabc'},
                    {'summary': 'abc te abc'},
                    {'summary': 'abc te'},
                ]
            ],
            [
                WildcardMatch('details.ip', '19*'), [
                    {'details': {'ip': '192.168.1.1'}},
                    {'details': {'ip': '19.168.1.1'}},
                ]
            ],
            [
                WildcardMatch('details.ip', '*1.0'), [
                    {'details': {'ip': '192.168.1.0'}},
                ]
            ],
        ]
        return tests


class TestWildcardMatchNegativeTestSuite(NegativeTestSuite):
    def query_tests(self):
        tests = [
            [
                WildcardMatch('summary', 'te*'), [
                    {'summary': 'example summary'},
                    {'summary': 'tabs 4 spaces'},
                ]
            ],
            [
                WildcardMatch('details.ip', '19*'), [
                    {'details': {'ip': '10.1.1.1'}},
                    {'details': {'ip': '2.168.1.192'}},
                    {'details': {'ip': '10.19.1.1'}},
                    {'details': {'ipaddress': '10.19.1.1'}},
                ]
            ],
        ]
        return tests
