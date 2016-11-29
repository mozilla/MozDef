from positive_test_suite import PositiveTestSuite
from negative_test_suite import NegativeTestSuite

import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), "../../lib"))
from query_models import RangeMatch


class TestRangeMatchPositiveTestSuite(PositiveTestSuite):
    def query_tests(self):
        begin_date = "2016-08-12T21:07:12.316450+00:00"
        end_date = "2016-08-13T21:07:12.316450+00:00"
        tests = {
            RangeMatch('utctimestamp', begin_date, end_date): [
                {'utctimestamp': '2016-08-12T21:07:12.316450+00:00'},
                {'utctimestamp': '2016-08-12T21:07:13.316450+00:00'},
                {'utctimestamp': '2016-08-12T23:04:12.316450+00:00'},
                {'utctimestamp': '2016-08-13T21:07:11.316450+00:00'},
                {'utctimestamp': '2016-08-13T21:07:12.316450+00:00'},
            ],
        }
        return tests


class TestTermMatchNegativeTestSuite(NegativeTestSuite):
    def query_tests(self):
        begin_date = "2016-08-12T21:07:12.316450+00:00"
        end_date = "2016-08-13T21:07:12.316450+00:00"
        tests = {
            RangeMatch('utctimestamp', begin_date, end_date): [
                {'utctimestamp': '2016-08-12T21:07:11.316450+00:00'},
                {'utctimestamp': '2016-08-12T21:07:12.316450+00:00'},
                {'utctimestamp': '2016-08-13T21:07:12.316450+00:00'},
                {'utctimestamp': '2016-08-13T21:07:13.316450+00:00'},
            ],
        }
        return tests
