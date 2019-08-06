import os

from tests.http_test_suite import HTTPTestSuite

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
        sample_config.configfile = os.path.join(os.path.dirname(__file__), 'index.conf')
        OptionParser.parse_args = mock.Mock(return_value=(sample_config, {}))

        from rest.index import application as rest_application
        self.application = rest_application
        super(RestTestSuite, self).setup()
