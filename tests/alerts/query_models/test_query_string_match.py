from positive_test_suite import PositiveTestSuite
from negative_test_suite import NegativeTestSuite

from models import QueryStringMatch


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
        }
        return tests
