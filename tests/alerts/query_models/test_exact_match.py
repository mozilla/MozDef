from positive_test_suite import PositiveTestSuite
from negative_test_suite import NegativeTestSuite

from models import ExactMatch


class TestExactMatchPositiveTestSuite(PositiveTestSuite):
    def query_tests(self):
        tests = {
            ExactMatch('summary', 'test'): [
                {'summary': 'test'},
            ],
            ExactMatch('summary', 'test conf'): [
                {'summary': 'test conf'},
                # {'summary': 'test'},# this is a problem, and should not pass
                # {'summary': 'conf'},# this is a problem, and should not pass
            ],
        }
        return tests


class TestExactMatchNegativeTestSuite(NegativeTestSuite):
    def query_tests(self):
        tests = {
            ExactMatch('summary', 'test'): [
                {'summary': 'testing'},
                {'summary': 'extestconf'},
            ],
            # ExactMatch('summary', 'test conf'): [
            #     {'summary': 'test'},
            #     {'summary': 'conf'},
            #     # {'summary': 'test inside conf'}, # this is a problem, and should pass
            #     # {'summary': 'extest config'}, # this is a problem, and should pass
            # ],
        }
        return tests
