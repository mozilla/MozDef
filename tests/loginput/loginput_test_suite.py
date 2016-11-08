import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), "../"))
from http_test_suite import HTTPTestSuite

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../loginput/"))
import index
reload(index)


class LoginputTestSuite(HTTPTestSuite):

    def setup(self):
        self.application = index.application
        super(LoginputTestSuite, self).setup()
