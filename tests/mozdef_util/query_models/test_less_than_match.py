from .positive_test_suite import PositiveTestSuite
from .negative_test_suite import NegativeTestSuite

from mozdef_util.query_models import LessThanMatch


class TestLessThanMatchPositiveTestSuite(PositiveTestSuite):
    def query_tests(self):
        boundry_date = "2016-08-12T21:07:12.316450+00:00"
        tests = [
            [
                LessThanMatch('utctimestamp', boundry_date), [
                    {'utctimestamp': '2015-08-12T21:07:12.316450+00:00'},
                    {'utctimestamp': '2016-02-12T21:07:12.316450+00:00'},
                    {'utctimestamp': '2016-08-11T21:07:12.316450+00:00'},
                    {'utctimestamp': '2016-08-12T20:07:12.316450+00:00'},
                ],
            ]
        ]
        return tests


class TestLessThanMatchNegativeTestSuite(NegativeTestSuite):
    def query_tests(self):
        boundry_date = "2016-08-12T21:07:12.316450+00:00"
        tests = [
            [
                LessThanMatch('utctimestamp', boundry_date), [
                    {'utctimestamp': '2017-08-12T21:07:12.316450+00:00'},
                    {'utctimestamp': '2016-09-12T21:07:12.316450+00:00'},
                    {'utctimestamp': '2016-08-14T21:07:12.316450+00:00'},
                    {'utctimestamp': '2016-08-12T23:07:12.316450+00:00'},
                    {'utctimestamp': '2016-08-12T21:08:12.316450+00:00'},
                    {'utctimestamp': '2016-08-12T21:07:13.316450+00:00'},
                    {'utctimestamp': '2016-08-12T21:07:12.416450+00:00'},
                    {'utctimestamp': '2016-08-12T21:07:12.316450+00:00'},
                ]
            ],
        ]
        return tests
