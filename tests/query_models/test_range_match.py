from positive_test_suite import PositiveTestSuite
from negative_test_suite import NegativeTestSuite

import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), "../../lib"))
from query_models import RangeMatch

# The weird thing here is that if events that have the exact same utctimestamp
# will not show up in either must or must_not. Updating to elasticsearch_dsl, we're
# going to use gte and lte, so inclusive, compared to exclusion in pyes.


class TestRangeMatchPositiveTestSuite(PositiveTestSuite):
    def query_tests(self):
        begin_date = "2016-08-12T21:07:12.316450+00:00"
        end_date = "2016-08-13T21:07:12.316450+00:00"
        tests = {
            RangeMatch('utctimestamp', begin_date, end_date): [
                # {'utctimestamp': '2016-08-12T21:07:12.316450+00:00'}, # uncomment when switched from pyes
                {'utctimestamp': '2016-08-12T21:07:13.316450+00:00'},
                {'utctimestamp': '2016-08-12T23:04:12.316450+00:00'},
                {'utctimestamp': '2016-08-13T21:07:11.316450+00:00'},
                # {'utctimestamp': '2016-08-13T21:07:12.316450+00:00'}, # uncomment when switched from pyes
                # this is because we are now including results that have the same value as either from or to
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
                # {'utctimestamp': '2016-08-12T21:07:12.316450+00:00'},
                # {'utctimestamp': '2016-08-13T21:07:12.316450+00:00'},
                {'utctimestamp': '2016-08-13T21:07:13.316450+00:00'},
            ],
        }
        return tests
