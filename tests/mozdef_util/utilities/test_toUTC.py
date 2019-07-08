from datetime import datetime, date
from dateutil.parser import parse

import importlib
import sys
import pytz

import tzlocal
from mozdef_util.utilities.toUTC import toUTC

UTC_TIMEZONE_COUNT = 0


def utc_timezone():
    ''' This is a mock function, so when we run tests
        we trick the system into thinking we're on UTC
        no matter what the real timezone is
    '''
    global UTC_TIMEZONE_COUNT
    UTC_TIMEZONE_COUNT += 1
    return pytz.timezone('UTC')


tzlocal.get_localzone = utc_timezone

if 'mozdef_util.utilities.toUTC' in sys.modules:
    importlib.reload(sys.modules['mozdef_util.utilities.toUTC'])


class TestToUTC():

    def result_is_datetime(self, result):
        assert type(result) == datetime

    def test_timezone_function_call_count(self):
        toUTC("2016-07-11 14:33:31.625443")
        toUTC("2016-07-12 14:33:31.625444")
        toUTC("2016-07-13 14:33:31.625445")
        toUTC("2016-07-14 14:33:31.625446")
        assert UTC_TIMEZONE_COUNT == 1

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

    def test_negative_string_float(self):
        result = toUTC("-86400.000000")
        self.result_is_datetime(result)
        assert str(result) == '1970-01-01 00:00:00+00:00'

    def test_negative_string_int(self):
        result = toUTC("-12345")
        self.result_is_datetime(result)
        assert str(result) == '1970-01-01 00:00:00+00:00'

    def test_zero_int(self):
        result = toUTC(0)
        self.result_is_datetime(result)
        assert str(result) == '1970-01-01 00:00:00+00:00'

    def test_zero_string_int(self):
        result = toUTC("0")
        self.result_is_datetime(result)
        assert str(result) == '1970-01-01 00:00:00+00:00'

    def test_zero_string_float(self):
        result = toUTC("0.0000")
        self.result_is_datetime(result)
        assert str(result) == '1970-01-01 00:00:00+00:00'

    def test_zero_float(self):
        result = toUTC(0.000000)
        assert str(result) == '1970-01-01 00:00:00+00:00'
