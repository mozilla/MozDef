import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), "../"))
from http_test_suite import HTTPTestSuite

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../rest/"))
import index
reload(index)


class RestTestSuite(HTTPTestSuite):

    def setup(self):
        self.application = index.application
        super(RestTestSuite, self).setup()
