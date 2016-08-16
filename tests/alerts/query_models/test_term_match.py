from positive_test_suite import PositiveTestSuite
from negative_test_suite import NegativeTestSuite

from models import TermMatch


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
        }
        return tests


class TestTermMatchNegativeTestSuite(NegativeTestSuite):
    def query_tests(self):
        tests = {
            TermMatch('summary', 'test'): [
                {'summary': 'example summary'},
                {'summary': 'example summary tes'},
                {'summary': 'testing'},
            ],
            TermMatch('summary', 'sum'): [
                {'summary': 'example test summary'},
                {'summary': 'example summary'},
                {'summary': 'summary test'},
                {'summary': 'summary'},
            ]
        }
        return tests
