from datetime import datetime, date
from dateutil.parser import parse

import sys
import os
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../../lib'))
from utilities.toUTC import toUTC


class TestToUTC():

    def result_is_datetime(self, result):
        assert type(result) == datetime

    def test_normal_date_str_with_default_timezone(self):
        result = toUTC("2016-07-13 14:33:31.625443")
        self.result_is_datetime(result)
        assert str(result) == '2016-07-13 14:33:31.625443+00:00'

    def test_normal_date_str_with_utc_timezone(self):
        result = toUTC("2016-07-13 22:33:31.625443+00:00")
        self.result_is_datetime(result)
        assert str(result) == '2016-07-13 22:33:31.625443+00:00'

    def test_normal_date_str_with_timezone(self):
        result = toUTC("2016-07-13 14:33:31.625443-08:00")
        self.result_is_datetime(result)
        assert str(result) == '2016-07-13 22:33:31.625443+00:00'

    def test_abnormal_date_str_without_timezone(self):
        result = toUTC("Jan  2 08:01:57")
        self.result_is_datetime(result)
        assert str(result) == str(date.today().year) + '-01-02 08:01:57+00:00'

    def test_abnormal_date_obj_with_timezone_in_date(self):
        result = toUTC(parse("2016-01-02 08:01:57+06:00"))
        self.result_is_datetime(result)
        assert str(result) == '2016-01-02 02:01:57+00:00'

    def test_long_epoch_without_timezone(self):
        result = toUTC(1468443523000000000)
        self.result_is_datetime(result)
        assert str(result) == '2016-07-13 20:58:43+00:00'

    def test_short_epoch_without_timezone(self):
        result = toUTC(1468443523)
        self.result_is_datetime(result)
        assert str(result) == '2016-07-13 20:58:43+00:00'

    def test_float_epoch(self):
        result = toUTC(1468443523.0)
        self.result_is_datetime(result)
        assert str(result) == '2016-07-13 20:58:43+00:00'

    def test_long_float_epoch(self):
        result = toUTC(1.468443523e+18)
        self.result_is_datetime(result)
        assert str(result) == '2016-07-13 20:58:43+00:00'

    def test_float_epoch_milliseconds(self):
        result = toUTC(1.468443523e+11)
        self.result_is_datetime(result)
        assert str(result) == '2016-07-13 20:58:43+00:00'
