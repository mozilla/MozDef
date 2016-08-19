from positive_test_suite import PositiveTestSuite
from negative_test_suite import NegativeTestSuite

import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), "../../lib"))
from query_models import PhraseMatch


class TestPhraseMatchPositiveTestSuite(PositiveTestSuite):
    def query_tests(self):
        tests = {
            PhraseMatch('summary', 'test run'): [
                {'summary': 'test run'},
                {'summary': 'this is test run source'},
                {'summary': 'this is test run'},
            ],
            PhraseMatch('summary', 'test'): [
                {'summary': 'test here'},
                {'summary': 'we are test here source'},
                {'summary': 'this is test'},
            ],
            PhraseMatch('summary', '/test/abc'): [
                {'summary': '/test/abc'},
                {'summary': '/test/abc/def'},
                {'summary': 'path /test/abc'},
            ],
        }
        return tests


class TestPhraseMatchNegativeTestSuite(NegativeTestSuite):
    def query_tests(self):
        tests = {
            PhraseMatch('summary', 'test run'): [
                {'summary': 'test sample run'},
                {'notes': 'test run'},
                {'summary': 'example test running'},
            ],
            PhraseMatch('summary', 'test abc'): [
                {'summary': 'example summary test'},
                {'notes': 'we are test here source'},
            ],
            PhraseMatch('summary', 'test'): [
                {'summary': 'we are testing'},
            ],
        }
        return tests
