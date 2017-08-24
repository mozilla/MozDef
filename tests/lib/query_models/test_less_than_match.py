from positive_test_suite import PositiveTestSuite
from negative_test_suite import NegativeTestSuite

import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), "../../lib"))
from query_models import LessThanMatch


class TestLessThanMatchPositiveTestSuite(PositiveTestSuite):
    def query_tests(self):
        boundry_date = "2016-08-12T21:07:12.316450+00:00"
        tests = {
            LessThanMatch('utctimestamp', boundry_date): [
                {'utctimestamp': '2015-08-12T21:07:12.316450+00:00'},
                {'utctimestamp': '2016-02-12T21:07:12.316450+00:00'},
                {'utctimestamp': '2016-08-11T21:07:12.316450+00:00'},
                {'utctimestamp': '2016-08-12T20:07:12.316450+00:00'},
            ],
        }
        return tests


class TestTermMatchNegativeTestSuite(NegativeTestSuite):
    def query_tests(self):
        boundry_date = "2016-08-12T21:07:12.316450+00:00"
        tests = {
            LessThanMatch('utctimestamp', boundry_date): [
                {'utctimestamp': '2017-08-12T21:07:12.316450+00:00'},
                {'utctimestamp': '2016-09-12T21:07:12.316450+00:00'},
                {'utctimestamp': '2016-08-14T21:07:12.316450+00:00'},
                {'utctimestamp': '2016-08-12T23:07:12.316450+00:00'},
                {'utctimestamp': '2016-08-12T21:08:12.316450+00:00'},
                {'utctimestamp': '2016-08-12T21:07:13.316450+00:00'},
                {'utctimestamp': '2016-08-12T21:07:12.416450+00:00'},
                {'utctimestamp': '2016-08-12T21:07:12.316450+00:00'},
            ],
        }
        return tests
