from positive_test_suite import PositiveTestSuite
from negative_test_suite import NegativeTestSuite

from models import MissingMatch


class TestMissingMatchPositiveTestSuite(PositiveTestSuite):
    def query_tests(self):
        tests = {
            MissingMatch('summary'): [
                {'host': 'testhost'},
                {'host': 'testhost', 'abc': 'def'}
            ],
        }
        return tests


class TestMissingMatchNegativeTestSuite(NegativeTestSuite):
    def query_tests(self):
        tests = {
            MissingMatch('summary'): [
                {'summary': 'example summary'},
                {'host': 'testhost', 'abc': 'def', 'summary': 'test'}
            ]
        }
        return tests
