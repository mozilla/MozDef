import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), "../"))
from http_test_suite import HTTPTestSuite

sys.path.append(os.path.join(os.path.dirname(__file__), "../../lib"))
from utilities.dot_dict import DotDict

import mock
from configlib import OptionParser

sample_config = DotDict()
sample_config.configfile = os.path.join(os.path.dirname(__file__), '../../rest/index.conf')
OptionParser.parse_args = mock.Mock(return_value=(sample_config, {}))

sys.path.append(os.path.join(os.path.dirname(__file__), "../../"))


class RestTestSuite(HTTPTestSuite):

    def setup(self):
        from rest import index
        self.application = index.application
        super(RestTestSuite, self).setup()
