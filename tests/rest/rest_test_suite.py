import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), "../"))
from http_test_suite import HTTPTestSuite

from mozdef_util.utilities.dot_dict import DotDict

import mock
from configlib import OptionParser


class RestTestDict(DotDict):
    @property
    def __dict__(self):
        return self


class RestTestSuite(HTTPTestSuite):

    def setup(self):
        sample_config = RestTestDict()
        sample_config.configfile = os.path.join(os.path.dirname(__file__), 'rest_index.conf')
        OptionParser.parse_args = mock.Mock(return_value=(sample_config, {}))

        from rest import index
        self.application = index.application
        super(RestTestSuite, self).setup()
