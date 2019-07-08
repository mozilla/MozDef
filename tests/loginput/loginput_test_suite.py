import sys
import os

from mozdef_util.utilities.dot_dict import DotDict

import mock
from configlib import OptionParser

sys.path.append(os.path.join(os.path.dirname(__file__), "../"))
from http_test_suite import HTTPTestSuite


class LoginputTestSuite(HTTPTestSuite):

    def setup(self):
        sample_config = DotDict()
        sample_config.configfile = os.path.join(os.path.dirname(__file__), 'index.conf')
        OptionParser.parse_args = mock.Mock(return_value=(sample_config, {}))
        from loginput import index
        self.application = index.application
        super(LoginputTestSuite, self).setup()
