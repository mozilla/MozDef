import pytest

import sys
import os
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../lib'))
from utilities import toUTC

from datetime import datetime
from dateutil.parser import parse

class TestToUTC():

  def result_is_datetime(self, result):
    assert type(result) == datetime

  def test_normal_date_str_with_default_timezone(self):
    result = toUTC("2016-07-13 14:33:31.625443")
    self.result_is_datetime(result)
    assert str(result) == '2016-07-13 14:33:31.625443+00:00'

  def test_normal_date_str_with_timezone(self):
    result = toUTC("2016-07-13 14:33:31.625443", "US/Pacific")
    self.result_is_datetime(result)
    assert str(result) == '2016-07-13 21:33:31.625443+00:00'

  def test_abnormal_date_str_without_timezone(self):
    result = toUTC("Jan  2 08:01:57")
    self.result_is_datetime(result)
    assert str(result) == '2016-01-02 08:01:57+00:00'

  def test_abnormal_date_str_with_timezone(self):
    result = toUTC("Jan  2 08:01:57", "US/Eastern")
    self.result_is_datetime(result)
    assert str(result) == '2016-01-02 13:01:57+00:00'

  def test_abnormal_date_obj_without_timezone(self):
    result = toUTC(parse("Jan  2 08:01:57"))
    self.result_is_datetime(result)
    assert str(result) == '2016-01-02 08:01:57+00:00'

  def test_abnormal_date_obj_with_timezone_in_date(self):
    result = toUTC(parse("2016-01-02 08:01:57+06:00"))
    self.result_is_datetime(result)
    assert str(result) == '2016-01-02 02:01:57+00:00'
