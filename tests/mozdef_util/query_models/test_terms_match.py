from .positive_test_suite import PositiveTestSuite
from .negative_test_suite import NegativeTestSuite

from mozdef_util.query_models import TermsMatch


class TestTermsMatchPositiveTestSuite(PositiveTestSuite):
    def query_tests(self):
        tests = [
            [
                TermsMatch('summary', ['test']), [
                    {'summary': 'test'},
                    {'summary': 'test summary'},
                    {'summary': 'example test summary'},
                    {'summary': 'example summary test'},
                ]
            ],
            [
                TermsMatch('summary', ['test', 'redfred']), [
                    {'summary': 'test'},
                    {'summary': 'redfred'},
                    {'summary': 'test summary'},
                    {'summary': 'example test summary'},
                    {'summary': 'example redfred summary test'},
                ]
            ],
        ]
        return tests


class TestTermsMatchNegativeTestSuite(NegativeTestSuite):
    def query_tests(self):
        tests = [
            [
                TermsMatch('summary', ['test']), [
                    {'summary': 'example summary'},
                    {'summary': 'example summary tes'},
                ]
            ],
            [
                TermsMatch('summary', ['test', 'exam']), [
                    {'summary': 'example summary'},
                    {'summary': 'example summary tes'},
                ]
            ]
        ]
        return tests
