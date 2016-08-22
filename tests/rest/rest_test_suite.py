import sys
import os

from webtest import TestApp

sys.path.append(os.path.join(os.path.dirname(__file__), "../"))
from unit_test_suite import UnitTestSuite
sys.path.append(os.path.join(os.path.dirname(__file__), "../../rest/"))
import index


class RestTestSuite(UnitTestSuite):

    def setup(self):
        super(RestTestSuite, self).setup()
        self.app = TestApp(index.application)

