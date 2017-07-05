import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), "../"))
from http_test_suite import HTTPTestSuite

sys.path.append(os.path.join(os.path.dirname(__file__), "../../lib"))
from utilities.dot_dict import DotDict

import mock
from configlib import OptionParser

sample_config = DotDict()
sample_config.configfile = os.path.join(os.path.dirname(__file__), '../../loginput/index.conf')
OptionParser.parse_args = mock.Mock(return_value=(sample_config, {}))

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../loginput/"))
import index
reload(index)


class LoginputTestSuite(HTTPTestSuite):

    def setup(self):
        self.application = index.application
        super(LoginputTestSuite, self).setup()
