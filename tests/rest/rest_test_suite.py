import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), "../"))
from http_test_suite import HTTPTestSuite

from mozdef_util.utilities.dot_dict import DotDict

import mock
from configlib import OptionParser
import importlib


class RestTestDict(DotDict):
    @property
    def __dict__(self):
        return self


class RestTestSuite(HTTPTestSuite):

    def setup(self):
        sample_config = RestTestDict()
        sample_config.configfile = os.path.join(os.path.dirname(__file__), 'index.conf')
        OptionParser.parse_args = mock.Mock(return_value=(sample_config, {}))

        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../rest"))
        import plugins
        importlib.reload(plugins)
        from rest import index

        self.application = index.application
        super(RestTestSuite, self).setup()
